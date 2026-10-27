import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

/// Displays the assigned partner's authorized GPS sample; never requests the
/// customer's own location permission or invents a delivery route.
class DeliveryPartnerMap extends StatefulWidget {
  const DeliveryPartnerMap({
    super.key,
    required this.location,
    this.tileProvider,
  });
  final Map<String, dynamic> location;
  final TileProvider? tileProvider;

  @override
  State<DeliveryPartnerMap> createState() => _DeliveryPartnerMapState();
}

class _DeliveryPartnerMapState extends State<DeliveryPartnerMap> {
  final controller = MapController();
  bool ready = false;
  bool follow = true;
  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant DeliveryPartnerMap oldWidget) {
    super.didUpdateWidget(oldWidget);
    final lat = double.tryParse('${widget.location['latitude']}');
    final lon = double.tryParse('${widget.location['longitude']}');
    if (ready &&
        follow &&
        lat != null &&
        lon != null &&
        lat.isFinite &&
        lon.isFinite &&
        lat.abs() <= 90 &&
        lon.abs() <= 180) {
      controller.move(LatLng(lat, lon), controller.camera.zoom);
    }
  }

  @override
  Widget build(BuildContext context) {
    final location = widget.location;
    final lat = double.tryParse('${location['latitude']}');
    final lon = double.tryParse('${location['longitude']}');
    if (lat == null ||
        lon == null ||
        !lat.isFinite ||
        !lon.isFinite ||
        lat.abs() > 90 ||
        lon.abs() > 180) {
      return const ListTile(title: Text('Partner location unavailable'));
    }
    final validUntil = DateTime.tryParse('${location['valid_until']}');
    if (validUntil != null && !validUntil.isAfter(DateTime.now())) {
      return const ListTile(
        title: Text('Waiting for a fresh partner location'),
      );
    }
    final point = LatLng(lat, lon);
    return SizedBox(
      height: 230,
      child: Stack(
        children: [
          FlutterMap(
            mapController: controller,
            options: MapOptions(
              initialCenter: point,
              initialZoom: 15,
              onMapReady: () {
                ready = true;
              },
              onPositionChanged: (_, gesture) {
                if (gesture) follow = false;
              },
            ),
            children: [
              TileLayer(
                tileProvider: widget.tileProvider,
                urlTemplate: const String.fromEnvironment(
                  'MAP_TILE_URL',
                  defaultValue:
                      'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                ),
                userAgentPackageName: 'com.quickbuddy.customer_app',
              ),
              MarkerLayer(
                markers: [
                  Marker(
                    point: point,
                    width: 44,
                    height: 44,
                    child: const Tooltip(
                      message: 'Delivery partner',
                      child: Icon(
                        Icons.delivery_dining,
                        size: 40,
                        color: Colors.deepPurple,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
          Positioned(
            bottom: 0,
            right: 0,
            child: ColoredBox(
              color: Theme.of(context).colorScheme.surface,
              child: const Padding(
                padding: EdgeInsets.all(4),
                child: Text(
                  '© OpenStreetMap contributors',
                  style: TextStyle(fontSize: 10),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
