import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:uuid/uuid.dart';

/// App-wide foreground calling. The backend decides who may join each call.
class DeliveryCallController extends ChangeNotifier
    with WidgetsBindingObserver {
  DeliveryCallController({required this.api, required this.tokens});
  final Dio api;
  final TokenStore tokens;
  Map<String, dynamic>? call;
  String? error;
  String status = 'Connecting…';
  bool _backgroundAudio = false;
  bool debugTracing = false;
  void _trace(String value) {
    if (debugTracing) debugPrint('QA CALL $value');
  }

  bool muted = false, speaker = false, busy = false;
  bool _foreground = true, _polling = false, _started = false, _closed = false;
  bool _remoteDescription = false;
  int _cursor = 0;
  int _failures = 0;
  Timer? _timer;
  Timer? _ringTimer;
  Timer? _connectionTimer;
  RTCPeerConnection? _peer;
  MediaStream? _microphone;
  final List<RTCIceCandidate> _pendingCandidates = [];
  Future<void> _sendQueue = Future.value();
  String? _preparingId;

  bool get incoming => call?['incoming'] == true;
  bool get ringing => call?['status'] == 'ringing';
  bool get connected => status == 'Connected';

  /// Transport counters for device QA; excludes audio, addresses and signaling payloads.
  Future<Map<String, num>> audioPacketCounts() async {
    num sent = 0, received = 0;
    final reports = await _peer?.getStats() ?? [];
    for (final report in reports) {
      final values = report.values;
      if (values['kind'] != 'audio' && values['mediaType'] != 'audio') continue;
      if (report.type == 'outbound-rtp')
        sent += (values['packetsSent'] as num?) ?? 0;
      if (report.type == 'inbound-rtp')
        received += (values['packetsReceived'] as num?) ?? 0;
    }
    return {'sent': sent, 'received': received};
  }

  void start() {
    if (_started) return;
    _started = true;
    _trace('listener started');
    const MethodChannel('quickbuddy/calling').setMethodCallHandler((
      event,
    ) async {
      if (event.method == 'endCall') await hangUp();
    });
    WidgetsBinding.instance.addObserver(this);
    _timer = Timer.periodic(
      const Duration(milliseconds: 900),
      (_) => unawaited(_poll()),
    );
  }

  void stop() {
    _timer?.cancel();
    _timer = null;
    _started = false;
    WidgetsBinding.instance.removeObserver(this);
    unawaited(hangUp());
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _trace('lifecycle ${state.name}');
    if (state == AppLifecycleState.resumed) _foreground = true;
    // Background capture requires the native ongoing-call service.
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.detached) {
      _foreground = false;
      if (call != null && !_backgroundAudio) unawaited(hangUp());
    }
    if (_foreground) unawaited(_poll());
  }

  void dismissError() {
    error = null;
    notifyListeners();
  }

  Future<MediaStream> _openMicrophone() async {
    // Ask before initializing WebRTC's native audio device module.
    bool? allowed;
    try {
      allowed = await const MethodChannel(
        'quickbuddy/calling',
      ).invokeMethod<bool>('requestMicrophone');
    } on MissingPluginException {
      /* Other supported platforms use WebRTC's permission flow. */
    }
    if (allowed == false) throw PlatformException(code: 'microphone_denied');
    try {
      _backgroundAudio =
          await const MethodChannel(
            'quickbuddy/calling',
          ).invokeMethod<bool>('startCallService') ??
          false;
    } catch (_) {
      _backgroundAudio = false;
    }
    return navigator.mediaDevices.getUserMedia({'audio': true, 'video': false});
  }

  Future<void> startCall(String deliveryId) async {
    if (busy || call != null) return;
    busy = true;
    error = null;
    notifyListeners();
    try {
      // Permission and capture must succeed before ringing the other person.
      _microphone = await _openMicrophone();
      if ((!_foreground && !_backgroundAudio) || _closed) {
        await _releaseMedia();
        return;
      }
      final response = await api.post(
        '/api/v1/calls',
        data: {'delivery_id': deliveryId},
      );
      call = Map<String, dynamic>.from(response.data);
      unawaited(_keepAwake(true));
      status = 'Calling…';
      _cursor = 0;
      _failures = 0;
      notifyListeners();
      await _preparePeer();
    } catch (e) {
      error = _message(e);
      await hangUp(keepError: true);
    } finally {
      busy = false;
      if (!_closed) notifyListeners();
    }
  }

  Future<void> answer() async {
    _trace('answer requested; busy=$busy incoming=$incoming');
    if (busy || call == null || !incoming) return;
    busy = true;
    error = null;
    notifyListeners();
    try {
      _stopRinging();
      _microphone = await _openMicrophone();
      _trace('answer microphone ready; foreground=$_foreground');
      if ((!_foreground && !_backgroundAudio) || call == null) {
        await _releaseMedia();
        return;
      }
      final id = call!['id'];
      final response = await api.post(
        '/api/v1/calls/$id/actions',
        data: {'action': 'accept'},
      );
      if (call?['id'] != id) return;
      call = Map<String, dynamic>.from(response.data);
      _trace('answer accepted by server');
      _stopRinging();
      status = 'Connecting…';
      if (call!['status'] != 'active') {
        await _finish();
        return;
      }
      await _preparePeer();
    } catch (e) {
      error = _message(e);
      await hangUp(keepError: true);
    } finally {
      busy = false;
      if (!_closed) notifyListeners();
    }
  }

  Future<void> hangUp({bool decline = false, bool keepError = false}) async {
    final id = call?['id'];
    // Stop the microphone immediately, even if the API cannot be reached.
    await _finish();
    if (!keepError) error = null;
    if (!_closed) notifyListeners();
    if (id != null) {
      try {
        await api.post(
          '/api/v1/calls/$id/actions',
          data: {'action': decline ? 'decline' : 'end'},
        );
      } catch (_) {
        /* Server expiry bounds an unreachable signaling session. */
      }
    }
  }

  Future<void> toggleMute() async {
    if (_microphone == null) return;
    muted = !muted;
    for (final track in _microphone!.getAudioTracks()) {
      track.enabled = !muted;
    }
    notifyListeners();
  }

  Future<void> toggleSpeaker() async {
    try {
      await Helper.setSpeakerphoneOn(!speaker);
      speaker = !speaker;
      notifyListeners();
    } catch (_) {
      error = 'Could not change the audio output.';
      notifyListeners();
    }
  }

  Future<void> _preparePeer() async {
    final id = call?['id'] as String?;
    if (id == null || _peer != null || _preparingId == id) return;
    _preparingId = id;
    try {
      final config = (await api.get('/api/v1/calls/$id')).data as Map;
      if (call?['id'] != id || (!_foreground && !_backgroundAudio)) return;
      final peer = await createPeerConnection({
        'iceServers': config['ice_servers'],
        'sdpSemantics': 'unified-plan',
      });
      if (call?['id'] != id) {
        await peer.close();
        await peer.dispose();
        return;
      }
      _peer = peer;
      _trace('peer created');
      if (call?['status'] == 'active') _armConnectionTimeout(id);
      peer.onIceCandidate = (candidate) {
        if (candidate.candidate?.isNotEmpty == true && call?['id'] == id) {
          _queueSignal(id, 'ice', candidate.toMap());
        }
      };
      peer.onConnectionState = (state) {
        _trace('peer state ${state.name}');
        if (call?['id'] != id) return;
        if (state == RTCPeerConnectionState.RTCPeerConnectionStateConnected) {
          _connectionTimer?.cancel();
          _connectionTimer = null;
          status = 'Connected';
        } else if (state ==
            RTCPeerConnectionState.RTCPeerConnectionStateFailed) {
          error = 'The audio connection failed. Please try calling again.';
          unawaited(hangUp(keepError: true));
        } else if (state ==
            RTCPeerConnectionState.RTCPeerConnectionStateDisconnected) {
          status = 'Reconnecting…';
          _connectionTimer ??= Timer(const Duration(seconds: 15), () {
            if (call?['id'] == id && !connected) {
              error = 'The audio connection was lost.';
              unawaited(hangUp(keepError: true));
            }
          });
        }
        if (!_closed) notifyListeners();
      };
      for (final track in _microphone!.getAudioTracks()) {
        await peer.addTrack(track, _microphone!);
      }
      await Helper.setSpeakerphoneOn(false);
      if (!incoming) {
        final offer = await peer.createOffer({
          'offerToReceiveAudio': true,
          'offerToReceiveVideo': false,
        });
        await peer.setLocalDescription(offer);
        await _postSignal(id, 'offer', offer.toMap());
      }
    } finally {
      if (_preparingId == id) _preparingId = null;
    }
  }

  void _armConnectionTimeout(String id) {
    _connectionTimer ??= Timer(const Duration(seconds: 30), () {
      if (call?['id'] == id && !connected) {
        error = 'Could not connect audio. Please try calling again.';
        unawaited(hangUp(keepError: true));
      }
    });
  }

  void _queueSignal(String id, String kind, Map<String, dynamic> payload) {
    _sendQueue = _sendQueue
        .then((_) async {
          if (call?['id'] == id) await _postSignal(id, kind, payload);
        })
        .catchError((Object e) {
          if (call?['id'] == id) {
            error = _message(e);
            unawaited(hangUp(keepError: true));
          }
        });
  }

  Future<void> _postSignal(
    String id,
    String kind,
    Map<String, dynamic> payload,
  ) async {
    await api.post(
      '/api/v1/calls/$id/signals',
      data: {
        'client_event_id': const Uuid().v4(),
        'kind': kind,
        'payload': payload,
      },
    );
  }

  int _idleTicks = 0;
  Future<void> _poll() async {
    if (_polling ||
        (!_foreground && !_backgroundAudio) ||
        _closed ||
        (busy && call == null)) {
      _trace(
        'poll skipped foreground=$_foreground busy=$busy polling=$_polling closed=$_closed',
      );
      return;
    }
    if (call == null && ++_idleTicks % 4 != 0) return;
    _polling = true;
    try {
      if (await tokens.accessToken() == null) {
        _trace('poll has no session');
        if (call != null) await _finish();
        return;
      }
      if (call == null) {
        final response = await api.get('/api/v1/calls/active');
        final items = response.data['items'] as List;
        _trace('incoming scan returned ${items.length} calls');
        if (items.isNotEmpty) {
          final found = Map<String, dynamic>.from(items.first);
          // A restarted app cannot resume a lost peer connection; close stale sessions.
          if (found['incoming'] != true || found['status'] != 'ringing') {
            await api.post(
              '/api/v1/calls/${found['id']}/actions',
              data: {'action': 'end'},
            );
            return;
          }
          call = found;
          _trace('incoming call received');
          unawaited(_keepAwake(true));
          _cursor = 0;
          error = null;
          status = 'Incoming call';
          unawaited(_playRing());
          HapticFeedback.vibrate();
          _ringTimer = Timer.periodic(const Duration(seconds: 3), (_) {
            if (_foreground && ringing && incoming) {
              unawaited(_playRing());
              HapticFeedback.vibrate();
            }
          });
        }
      } else {
        final id = call!['id'];
        final response = await api.get(
          '/api/v1/calls/$id/signals',
          queryParameters: {'after': _cursor},
        );
        if (call?['id'] != id) return;
        call = Map<String, dynamic>.from(response.data['call']);
        if (!{'ringing', 'active'}.contains(call!['status'])) {
          final ending = call!['status'];
          await _finish();
          error = ending == 'declined'
              ? 'Call declined.'
              : ending == 'missed'
              ? 'No answer.'
              : 'Call ended.';
        } else {
          if (call!['status'] == 'active' && _peer != null && !connected) {
            _armConnectionTimeout(id);
          }
          for (final raw in response.data['items'] as List) {
            if (call?['id'] != id) break;
            final kind = raw['kind'];
            final data = Map<String, dynamic>.from(raw['payload']);
            // Keep the offer cursor until the recipient has explicitly accepted.
            if (incoming && ringing) break;
            final peer = _peer;
            if (peer == null) break;
            if (kind == 'offer' || kind == 'answer') {
              _trace('received $kind');
              await peer.setRemoteDescription(
                RTCSessionDescription(data['sdp'], data['type']),
              );
              _remoteDescription = true;
              for (final candidate in _pendingCandidates) {
                await peer.addCandidate(candidate);
              }
              _pendingCandidates.clear();
              if (kind == 'offer') {
                final answer = await peer.createAnswer({
                  'offerToReceiveAudio': true,
                });
                await peer.setLocalDescription(answer);
                await _postSignal(id, 'answer', answer.toMap());
              }
              if (!connected) status = 'Connecting…';
            } else if (kind == 'ice') {
              final candidate = RTCIceCandidate(
                data['candidate'],
                data['sdpMid'],
                data['sdpMLineIndex'],
              );
              if (_remoteDescription) {
                await peer.addCandidate(candidate);
              } else {
                _pendingCandidates.add(candidate);
              }
            }
            _cursor = raw['id'] as int;
          }
        }
      }
      _failures = 0;
    } catch (e) {
      _trace('poll error: ${_message(e)}');
      if (call != null && ++_failures >= 3) {
        error = 'Call disconnected. Check your internet connection.';
        await hangUp(keepError: true);
      }
    } finally {
      _polling = false;
      if (!_closed) notifyListeners();
    }
  }

  Future<void> _keepAwake(bool value) async {
    try {
      await const MethodChannel(
        'quickbuddy/calling',
      ).invokeMethod<void>(value ? 'keepAwake' : 'releaseAwake');
    } catch (_) {
      /* Audio remains usable if the display policy cannot change. */
    }
  }

  Future<void> _playRing() async {
    try {
      await const MethodChannel(
        'quickbuddy/calling',
      ).invokeMethod<void>('ring');
    } catch (_) {
      /* Vibration remains available. */
    }
  }

  void _stopRinging() {
    _ringTimer?.cancel();
    _ringTimer = null;
    unawaited(
      const MethodChannel(
        'quickbuddy/calling',
      ).invokeMethod<void>('stopRinging').catchError((Object _) {}),
    );
  }

  Future<void> _releaseMedia() async {
    final microphone = _microphone;
    _microphone = null;
    if (microphone != null) {
      for (final track in microphone.getTracks()) {
        await track.stop();
      }
      await microphone.dispose();
    }
    final peer = _peer;
    _peer = null;
    if (peer != null) {
      await peer.close();
      await peer.dispose();
    }
  }

  Future<void> _finish() async {
    _backgroundAudio = false;
    unawaited(
      const MethodChannel(
        'quickbuddy/calling',
      ).invokeMethod<void>('stopCallService').catchError((Object _) {}),
    );
    unawaited(_keepAwake(false));
    _connectionTimer?.cancel();
    _connectionTimer = null;
    call = null;
    _stopRinging();
    _cursor = 0;
    _pendingCandidates.clear();
    _remoteDescription = false;
    muted = false;
    speaker = false;
    await _releaseMedia();
  }

  @override
  void dispose() {
    _closed = true;
    _timer?.cancel();
    _stopRinging();
    WidgetsBinding.instance.removeObserver(this);
    unawaited(hangUp());
    super.dispose();
  }
}

String _message(Object error) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map && data['error'] is Map)
      return '${data['error']['message']}';
    return 'Could not reach calling. Check your internet connection.';
  }
  if (error is PlatformException)
    return 'Microphone access is required. Allow it in app settings and try again.';
  return 'Could not start audio. Check microphone permission and try again.';
}

class DeliveryCallButton extends StatelessWidget {
  const DeliveryCallButton({
    super.key,
    required this.controller,
    required this.deliveryId,
    required this.label,
  });
  final DeliveryCallController controller;
  final String deliveryId, label;
  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: controller,
    builder: (context, _) => OutlinedButton.icon(
      icon: const Icon(Icons.call),
      label: Text(label),
      onPressed: controller.busy || controller.call != null
          ? null
          : () => controller.startCall(deliveryId),
    ),
  );
}

class DeliveryCallOverlay extends StatefulWidget {
  const DeliveryCallOverlay({
    super.key,
    required this.controller,
    required this.child,
    required this.peerLabel,
  });
  final DeliveryCallController controller;
  final Widget child;
  final String peerLabel;
  @override
  State<DeliveryCallOverlay> createState() => _DeliveryCallOverlayState();
}

class _DeliveryCallOverlayState extends State<DeliveryCallOverlay> {
  @override
  void initState() {
    super.initState();
    widget.controller.start();
  }

  @override
  void dispose() {
    widget.controller.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Overlay.wrap(
    child: ListenableBuilder(
      listenable: widget.controller,
      builder: (context, _) {
        final c = widget.controller;
        return Stack(
          children: [
            widget.child,
            if (c.call != null)
              Positioned.fill(
                child: Material(
                  color: const Color(0xFF211B4C),
                  child: SafeArea(
                    child: Center(
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.call,
                              color: Colors.white,
                              size: 64,
                            ),
                            const SizedBox(height: 24),
                            Text(
                              widget.peerLabel,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 28,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              c.status,
                              style: const TextStyle(
                                color: Colors.white70,
                                fontSize: 18,
                              ),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              'Internet audio call',
                              style: TextStyle(color: Colors.white60),
                            ),
                            const SizedBox(height: 32),
                            if (c.incoming && c.ringing)
                              Wrap(
                                spacing: 20,
                                runSpacing: 12,
                                alignment: WrapAlignment.center,
                                children: [
                                  FilledButton.icon(
                                    style: FilledButton.styleFrom(
                                      backgroundColor: Colors.green,
                                    ),
                                    onPressed: c.busy ? null : c.answer,
                                    icon: const Icon(Icons.call),
                                    label: const Text('Answer'),
                                  ),
                                  FilledButton.icon(
                                    style: FilledButton.styleFrom(
                                      backgroundColor: Colors.red,
                                    ),
                                    onPressed: () => c.hangUp(decline: true),
                                    icon: const Icon(Icons.call_end),
                                    label: const Text('Decline'),
                                  ),
                                ],
                              )
                            else ...[
                              Wrap(
                                spacing: 16,
                                alignment: WrapAlignment.center,
                                children: [
                                  IconButton.filled(
                                    tooltip: c.muted ? 'Unmute' : 'Mute',
                                    onPressed: c.toggleMute,
                                    icon: Icon(
                                      c.muted ? Icons.mic_off : Icons.mic,
                                    ),
                                  ),
                                  IconButton.filled(
                                    tooltip: c.speaker
                                        ? 'Use earpiece'
                                        : 'Use speaker',
                                    onPressed: c.toggleSpeaker,
                                    icon: Icon(
                                      c.speaker
                                          ? Icons.volume_up
                                          : Icons.hearing,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 20),
                              FilledButton.icon(
                                style: FilledButton.styleFrom(
                                  backgroundColor: Colors.red,
                                ),
                                onPressed: () => c.hangUp(),
                                icon: const Icon(Icons.call_end),
                                label: const Text('End call'),
                              ),
                            ],
                            if (c.busy)
                              const Padding(
                                padding: EdgeInsets.all(16),
                                child: CircularProgressIndicator(
                                  color: Colors.white,
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            if (c.error != null)
              Positioned(
                left: 16,
                right: 16,
                bottom: 24,
                child: SafeArea(
                  child: Material(
                    elevation: 8,
                    borderRadius: BorderRadius.circular(12),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        children: [
                          Expanded(child: Text(c.error!)),
                          IconButton(
                            tooltip: 'Dismiss call message',
                            onPressed: c.dismissError,
                            icon: const Icon(Icons.close),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
          ],
        );
      },
    ),
  );
}
