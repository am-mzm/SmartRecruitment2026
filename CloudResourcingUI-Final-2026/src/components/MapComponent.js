import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Import the default icon image for the marker
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import markerRetina from 'leaflet/dist/images/marker-icon-2x.png';

// Fix the default marker icon issues with webpack
const DefaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerRetina,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

const MapComponent = () => {
  const torontoCoordinates = [43.6440, -79.3857];
  const ypsilantiCoordinates = [42.247333, -83.615556];

  return (
    <div style={styles.mapContainer}>
      <MapContainer center={torontoCoordinates} zoom={5} style={styles.map}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={torontoCoordinates}>
          <Popup>
            200 Front St. W., Toronto
          </Popup>
        </Marker>
        <Marker position={ypsilantiCoordinates}>
          <Popup>
            9621 W Avondale Cir, Ypsilanti, MI 48198
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
};

const styles = {
  mapContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    width: '100vw',
  },
  map: {
    height: '50vh',
    width: '50vw',
  },
};

export default MapComponent;
