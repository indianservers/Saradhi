// Synthetic microphone peer for the Android WebRTC transport test.
// Uses a fresh headless browser, never a user's browser profile.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const { chromium } = require(path.join(root, '.local/calling-qa/node_modules/playwright-core'));

(async () => {
  const defines = JSON.parse(fs.readFileSync(path.join(root, '.secrets/device-call-customer.json'), 'utf8'));
  const browser = await chromium.launch({
    executablePath: process.env.QA_CHROMIUM_PATH,
    headless: true,
    args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream',
      '--autoplay-policy=no-user-gesture-required', '--disable-features=WebRtcHideLocalIpsWithMdns'],
  });
  try {
    const context = await browser.newContext({ permissions: ['microphone'] });
    const page = await context.newPage();
    // A real same-origin navigation gives Chromium the correct loopback address space.
    await page.goto('http://127.0.0.1:18002/health/live');
    page.on('console', message => { if (message.text().startsWith('QA ') || message.type() === 'error') console.log(message.text()); });
    console.log('QA browser ready; create .local/calling-qa/go when the Android recipient is ready.');
    const marker = path.join(root, '.local/calling-qa/go');
    while (!fs.existsSync(marker)) await new Promise(resolve => setTimeout(resolve, 500));
    fs.unlinkSync(marker);
    await page.evaluate(async (defines) => {
      const base = 'http://127.0.0.1:18002';
      let token;
      async function api(url, method = 'GET', body) {
        const response = await fetch(base + '/api/v1' + url, {
          method, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
          ...(body === undefined ? {} : { body: JSON.stringify(body) }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(`Calling API ${response.status}: ${data.error?.message || 'request failed'}`);
        return data;
      }
      const auth = await api('/auth/login', 'POST', { email: defines.QA_EMAIL, password: defines.QA_PASSWORD });
      token = auth.access_token;
      const old = await api('/calls/active');
      for (const call of old.items) await api(`/calls/${call.id}/actions`, 'POST', { action: 'end' });
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      try {
        for (let round = 0; round < 2; round++) {
          const initiator = round === 0;
          let call;
          const start = Date.now();
          if (initiator) call = await api('/calls', 'POST', { delivery_id: defines.QA_DELIVERY_ID });
          else {
            while (!call && Date.now() - start < 120000) {
              const active = await api('/calls/active');
              call = active.items.find(c => c.incoming && c.status === 'ringing');
              if (!call) await new Promise(resolve => setTimeout(resolve, 300));
            }
            if (!call) throw new Error('Reverse call did not arrive');
            call = await api(`/calls/${call.id}/actions`, 'POST', { action: 'accept' });
          }
          const config = await api(`/calls/${call.id}`);
          const peer = new RTCPeerConnection({ iceServers: config.ice_servers });
          let signalError;
          async function send(kind, payload) {
            await api(`/calls/${call.id}/signals`, 'POST', { kind, payload, client_event_id: crypto.randomUUID() });
          }
          peer.onicecandidate = event => {
            if (event.candidate) send('ice', {
              candidate: event.candidate.candidate, sdpMid: event.candidate.sdpMid,
              sdpMLineIndex: event.candidate.sdpMLineIndex,
            }).catch(error => { signalError = error; });
          };
          for (const track of stream.getAudioTracks()) peer.addTrack(track, stream);
          if (initiator) {
            const offer = await peer.createOffer(); await peer.setLocalDescription(offer);
            await send('offer', { type: offer.type, sdp: offer.sdp });
          }
          let cursor = 0, connectedAt = null, checked = false;
          const pending = [];
          try {
            while (Date.now() - start < 120000) {
              if (signalError) throw signalError;
              const result = await api(`/calls/${call.id}/signals?after=${cursor}`);
              if (!['ringing', 'active'].includes(result.call.status)) {
                if (!checked) throw new Error('Call ended before audio packet verification');
                break;
              }
              for (const event of result.items) {
                if (event.kind === 'offer' || event.kind === 'answer') {
                  await peer.setRemoteDescription(event.payload);
                  for (const candidate of pending.splice(0)) await peer.addIceCandidate(candidate);
                  if (event.kind === 'offer') {
                    const answer = await peer.createAnswer(); await peer.setLocalDescription(answer);
                    await send('answer', { type: answer.type, sdp: answer.sdp });
                  }
                } else if (peer.remoteDescription) await peer.addIceCandidate(event.payload);
                else pending.push(event.payload);
                cursor = event.id;
              }
              if (peer.connectionState === 'connected' && connectedAt === null) connectedAt = Date.now();
              if (connectedAt && !checked && Date.now() - connectedAt > 5000) {
                let sent = 0, received = 0;
                (await peer.getStats()).forEach(report => {
                  if (report.kind !== 'audio') return;
                  if (report.type === 'outbound-rtp') sent += report.packetsSent || 0;
                  if (report.type === 'inbound-rtp') received += report.packetsReceived || 0;
                });
                if (sent <= 0 || received <= 0) throw new Error('Audio packets were not bidirectional');
                checked = true; console.log(`QA BROWSER AUDIO ROUND ${round}: sent=${sent} received=${received}`);
              }
              if (initiator && checked && Date.now() - connectedAt > 30000) {
                await api(`/calls/${call.id}/actions`, 'POST', { action: 'end' }); break;
              }
              await new Promise(resolve => setTimeout(resolve, 250));
            }
            if (!checked) throw new Error('Audio connection timed out');
          } finally { peer.close(); }
          console.log(`QA BROWSER HANGUP ROUND ${round} passed`);
        }
      } finally { stream.getTracks().forEach(track => track.stop()); }
    }, defines);
    console.log('QA browser bidirectional call tests passed');
  } finally { await browser.close(); }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
