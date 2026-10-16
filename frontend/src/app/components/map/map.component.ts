import {
  Component, OnInit, OnDestroy, ElementRef, ViewChild, AfterViewInit,
  ChangeDetectorRef, HostListener
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  Viewer, Ion, Color, GeoJsonDataSource,
  ScreenSpaceEventHandler, ScreenSpaceEventType, defined,
  LabelStyle, VerticalOrigin, NearFarScalar,
  ColorMaterialProperty, HeightReference, HeadingPitchRange, Math as CesiumMath,
  Cartesian2, Cartesian3, BoundingSphere, DistanceDisplayCondition
} from 'cesium';
import { environment } from '../../../environments/environment';
import { ApiService, County, Facility } from '../../services/api.service';
import { StateService } from '../../services/state.service';

Ion.defaultAccessToken = environment.cesiumToken;

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css'],
})
export class MapComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('cesiumContainer', { static: true }) container!: ElementRef;

  private viewer?: Viewer;
  private handler?: ScreenSpaceEventHandler;
  private boundaryDataSource?: GeoJsonDataSource;
  private sublocationSource?: GeoJsonDataSource;
  private facilitySource?: GeoJsonDataSource;
  private roadSource?: GeoJsonDataSource;
  private pinDataSource?: GeoJsonDataSource;
  private selectedEntity?: any;

  counties: County[] = [];
  filteredCounties: County[] = [];
  facilities: Facility[] = [];
  countyStats: any = null;

  selectedCounty: County | null = null;
  searchTerm = '';
  showSuggestions = false;
  showSublocations = false;
  showFacilities = false;
  showRoads = false;

  statusMessage = 'Loading...';
  loading = true;
  loadingPercent = 0;
  loadingMessage = 'Starting up...';

  theme: 'light' | 'dark' = 'light';
  sidebarOpen = true;

  measureMode = false;
  measurePoints: Array<{ lon: number; lat: number }> = [];
  measureResult = '';

  compareMode = false;
  compareCounty: County | null = null;
  compareResult: any = null;

  nearestMode = false;
  nearestResult: any = null;

  pinMode = false;
  pins: Array<{ lon: number; lat: number; label: string }> = [];

  presentationMode = false;

  roadCount = 0;
  facilityCount = 0;
  sublocationCount = 0;

  featureInfo: { title: string; items: Array<{ label: string; value: string }> } | null = null;

  mouseLon = 0;
  mouseLat = 0;
  mouseElevation = 0;
  nairobiDistance = 0;
  private nairobi = { lat: -1.2864, lon: 36.8172 };

  constructor(
    private api: ApiService,
    private state: StateService,
    private cdr: ChangeDetectorRef
  ) {}

  @HostListener('document:keydown', ['$event'])
  handleKeyboard(event: KeyboardEvent) {
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
      event.preventDefault();
      const el = document.getElementById('search-input');
      if (el) (el as HTMLInputElement).focus();
    }
    if (event.key === 'Escape') {
      if (this.presentationMode) { this.presentationMode = false; this.sidebarOpen = true; }
      this.showSuggestions = false;
      this.measureMode = false;
      this.measurePoints = [];
      this.measureResult = '';
      this.cdr.detectChanges();
    }
  }

  ngOnInit() {
    this.state.theme.subscribe(t => { this.theme = t; this.cdr.detectChanges(); });
    this.state.sidebarOpen.subscribe(o => { this.sidebarOpen = o; this.cdr.detectChanges(); });

    this.api.getCounties().then(
      (data) => {
        this.counties = data;
        this.filteredCounties = data;
        this.statusMessage = data.length + ' counties loaded';
        this.cdr.detectChanges();
      },
      (err) => {
        console.error(err);
        this.statusMessage = 'Counties failed';
        this.cdr.detectChanges();
      }
    );
    this.loadingPercent = 10;
  }

  async ngAfterViewInit() {
    try {
      this.loadingMessage = 'Starting 3D globe...';
      this.loadingPercent = 20;
      this.cdr.detectChanges();

      this.viewer = new Viewer(this.container.nativeElement, {
        baseLayerPicker: false, geocoder: false, homeButton: false,
        sceneModePicker: false, navigationHelpButton: false,
        timeline: false, animation: false, fullscreenButton: false,
        infoBox: false, selectionIndicator: false
      });

      (this.viewer.cesiumWidget.creditContainer as HTMLElement).style.display = 'none';

      const scene = this.viewer.scene;
      scene.skyAtmosphere!.show = true;
      scene.globe!.showGroundAtmosphere = true;
      scene.globe!.enableLighting = false;
      scene.globe!.baseColor = Color.WHITE;

      this.loadingMessage = 'Loading county boundaries...';
      this.loadingPercent = 40;
      this.cdr.detectChanges();

      const boundaries = await this.api.getBoundaries();

      this.boundaryDataSource = await GeoJsonDataSource.load(boundaries, {
        stroke: Color.WHITE,
        strokeWidth: 2,
        fill: Color.fromCssColorString('#2d7d46').withAlpha(0.3),
      });

      this.boundaryDataSource.entities.values.forEach((entity: any) => {
        if (entity.polygon) {
          entity.polygon.distanceDisplayCondition = new DistanceDisplayCondition(50000, 10000000);
          const props = entity.properties;
          const name = props ? props['name']?.getValue() : null;
          if (name) {
            entity.label = {
              text: name.toUpperCase(),
              font: '900 22px system-ui, sans-serif',
              style: LabelStyle.FILL_AND_OUTLINE,
              outlineWidth: 4,
              outlineColor: Color.WHITE,
              fillColor: Color.fromCssColorString('#1a3a1f'),
              verticalOrigin: VerticalOrigin.CENTER,
              heightReference: HeightReference.CLAMP_TO_GROUND,
              scaleByDistance: new NearFarScalar(100, 1.2, 2000000, 0.7),
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
              showBackground: true,
              backgroundColor: Color.WHITE.withAlpha(0.75),
              backgroundPadding: new Cartesian2(10, 6),
            };
          }
        }
        if (entity.polyline) {
          entity.polyline.material = new ColorMaterialProperty(Color.WHITE.withAlpha(0.9));
          entity.polyline.width = 2;
        }
      });

      this.loadingPercent = 70;
      this.cdr.detectChanges();

      await this.viewer.dataSources.add(this.boundaryDataSource);
      await this.viewer.zoomTo(this.boundaryDataSource);

      this.loadingPercent = 100;
      this.loadingMessage = 'Ready';
      this.cdr.detectChanges();
      setTimeout(() => { this.loading = false; this.cdr.detectChanges(); }, 400);

      this.setupHandlers();
    } catch (err) {
      console.error('Init failed:', err);
      this.loadingMessage = 'Failed to load';
      this.cdr.detectChanges();
    }
  }

  private setupHandlers() {
    const canvas = this.viewer!.scene.canvas;
    this.handler = new ScreenSpaceEventHandler(canvas);

    this.handler.setInputAction((event: any) => {
      if (this.measureMode) {
        const cartesian = this.viewer!.camera.pickEllipsoid(event.position, this.viewer!.scene.globe.ellipsoid);
        if (cartesian) {
          const carto = this.viewer!.scene.globe.ellipsoid.cartesianToCartographic(cartesian);
          this.measurePoints.push({
            lon: CesiumMath.toDegrees(carto.longitude),
            lat: CesiumMath.toDegrees(carto.latitude)
          });
          this.computeMeasure();
          this.cdr.detectChanges();
        }
        return;
      }

      if (this.nearestMode) {
        const cartesian = this.viewer!.camera.pickEllipsoid(event.position, this.viewer!.scene.globe.ellipsoid);
        if (cartesian) {
          const carto = this.viewer!.scene.globe.ellipsoid.cartesianToCartographic(cartesian);
          this.findNearest(CesiumMath.toDegrees(carto.latitude), CesiumMath.toDegrees(carto.longitude));
        }
        return;
      }

      if (this.pinMode) {
        const cartesian = this.viewer!.camera.pickEllipsoid(event.position, this.viewer!.scene.globe.ellipsoid);
        if (cartesian) {
          const carto = this.viewer!.scene.globe.ellipsoid.cartesianToCartographic(cartesian);
          this.dropPin(CesiumMath.toDegrees(carto.longitude), CesiumMath.toDegrees(carto.latitude));
        }
        return;
      }

      const picked = this.viewer!.scene.pick(event.position);
      if (defined(picked) && picked.id) {
        const props = picked.id.properties;
        const name = props ? props['name']?.getValue() : null;
        const type = props ? props['type']?.getValue() : null;
        const highway = props ? props['highway']?.getValue() : null;
        const county = props ? props['county']?.getValue() : null;

        if (highway) {
          this.featureInfo = {
            title: name || 'Unnamed road',
            items: [
              { label: 'Type', value: highway },
              { label: 'Name', value: name || '—' },
            ]
          };
          this.cdr.detectChanges();
          return;
        }

        if (type && name) {
          this.featureInfo = {
            title: name,
            items: [
              { label: 'Type', value: type },
              { label: 'County', value: county || '—' },
            ]
          };
          this.cdr.detectChanges();
          return;
        }

        if (name) {
          const match = this.counties.find(c => c.name.toLowerCase() === name.toLowerCase());
          if (this.compareMode && this.selectedCounty && match && match.id !== this.selectedCounty.id) {
            this.compareCounty = match;
            this.runComparison();
            this.cdr.detectChanges();
            return;
          }
          this.selectedCounty = match || null;
          this.highlightEntity(picked.id);
          if (this.selectedCounty) {
            this.loadStats(this.selectedCounty);
            this.loadFacilities(this.selectedCounty.name);
          }
          this.cdr.detectChanges();
        }
      } else {
        this.selectedCounty = null;
        this.featureInfo = null;
        this.highlightEntity(null);
        this.cdr.detectChanges();
      }
    }, ScreenSpaceEventType.LEFT_CLICK);

    this.handler.setInputAction((event: any) => {
      const cartesian = this.viewer!.camera.pickEllipsoid(event.endPosition, this.viewer!.scene.globe.ellipsoid);
      if (cartesian) {
        const carto = this.viewer!.scene.globe.ellipsoid.cartesianToCartographic(cartesian);
        this.mouseLon = CesiumMath.toDegrees(carto.longitude);
        this.mouseLat = CesiumMath.toDegrees(carto.latitude);
        this.mouseElevation = this.viewer!.scene.globe.getHeight(carto) || 0;
        this.updateNairobiDistance(this.mouseLat, this.mouseLon);
        this.cdr.detectChanges();
      }
    }, ScreenSpaceEventType.MOUSE_MOVE);
  }

  private computeMeasure() {
    if (this.measurePoints.length < 2) {
      this.measureResult = this.measurePoints.length === 1 ? 'Click second point' : '';
      return;
    }
    let total = 0;
    for (let i = 1; i < this.measurePoints.length; i++) {
      const a = this.measurePoints[i - 1];
      const b = this.measurePoints[i];
      const R = 6371;
      const dLat = (b.lat - a.lat) * Math.PI / 180;
      const dLon = (b.lon - a.lon) * Math.PI / 180;
      const lat1 = a.lat * Math.PI / 180;
      const lat2 = b.lat * Math.PI / 180;
      const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
      total += 2 * R * Math.asin(Math.sqrt(h));
    }
    this.measureResult = total.toFixed(2) + ' km';
  }

  private updateNairobiDistance(lat: number, lon: number) {
    const R = 6371;
    const dLat = (lat - this.nairobi.lat) * Math.PI / 180;
    const dLon = (lon - this.nairobi.lon) * Math.PI / 180;
    const lat1 = this.nairobi.lat * Math.PI / 180;
    const lat2 = lat * Math.PI / 180;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
    this.nairobiDistance = 2 * R * Math.asin(Math.sqrt(h));
  }

  private highlightEntity(entity: any) {
    if (this.selectedEntity && this.selectedEntity.polygon) {
      this.selectedEntity.polygon.material = new ColorMaterialProperty(
        Color.fromCssColorString('#2d7d46').withAlpha(0.3)
      );
    }
    if (entity && entity.polygon) {
      entity.polygon.material = new ColorMaterialProperty(
        Color.fromCssColorString('#ffcc00').withAlpha(0.5)
      );
      this.selectedEntity = entity;
    } else {
      this.selectedEntity = null;
    }
  }

  onSearchInput(term: string) {
    this.searchTerm = term;
    if (!term.trim()) { this.filteredCounties = this.counties; this.showSuggestions = false; return; }
    const lower = term.toLowerCase();
    this.filteredCounties = this.counties.filter(c =>
      c.name.toLowerCase().includes(lower) || c.capital.toLowerCase().includes(lower) || c.code.includes(term)
    );
    this.showSuggestions = true;
  }

  onSearchSubmit() {
    this.showSuggestions = false;
    if (this.filteredCounties.length > 0) this.flyToCounty(this.filteredCounties[0]);
  }

  selectFromSidebar(county: County) {
    this.showSuggestions = false;
    this.flyToCounty(county);
  }

  private flyToCounty(county: County) {
    const entities = this.boundaryDataSource?.entities.values || [];
    const target = entities.find((e: any) => {
      const props = e.properties;
      const n = props ? props['name']?.getValue() : null;
      return n && n.toLowerCase() === county.name.toLowerCase();
    });

    if (target && target.polygon) {
      const hierarchy = target.polygon.hierarchy?.getValue();
      const positions: Cartesian3[] = hierarchy?.positions || [];
      if (positions.length > 0) {
        const sphere = BoundingSphere.fromPoints(positions);
        this.viewer!.camera.flyToBoundingSphere(sphere, {
          duration: 2.0,
          offset: new HeadingPitchRange(0, -Math.PI / 4, sphere.radius * 3),
        });
      }
      this.highlightEntity(target);
    }

    this.selectedCounty = county;
    this.statusMessage = 'Zoomed to ' + county.name;
    this.loadStats(county);
    this.loadFacilities(county.name);
    this.cdr.detectChanges();
  }

  private async loadStats(county: County) {
    try { this.countyStats = await this.api.getCountyStats(county.id); } catch { this.countyStats = null; }
    this.cdr.detectChanges();
  }

  private async loadFacilities(countyName: string) {
    try { this.facilities = await this.api.getFacilities(countyName); } catch { this.facilities = []; }
    this.cdr.detectChanges();
  }

  async toggleRoads() {
    this.showRoads = !this.showRoads;
    if (!this.showRoads) {
      if (this.roadSource) { this.viewer!.dataSources.remove(this.roadSource, true); this.roadSource = undefined; }
      this.roadCount = 0;
      this.statusMessage = 'Roads off';
      this.cdr.detectChanges();
      return;
    }
    try {
      this.statusMessage = 'Loading roads (visible area only)...';
      this.cdr.detectChanges();

      // Get current map view bounding box
      const camera = this.viewer!.camera;
      const rect = camera.computeViewRectangle();
      let bbox: any = undefined;
      if (rect) {
        bbox = {
          minLat: CesiumMath.toDegrees(rect.south),
          maxLat: CesiumMath.toDegrees(rect.north),
          minLon: CesiumMath.toDegrees(rect.west),
          maxLon: CesiumMath.toDegrees(rect.east),
        };
      }

      const roads = await this.api.getRoads(bbox);
      const fc = {
        type: 'FeatureCollection',
        features: roads.features.map((f: any) => {
          const hw = f.properties.highway;
          let color = '#9ca3af';
          let width = 2;
          if (hw === 'motorway') { color = '#dc2626'; width = 6; }
          else if (hw === 'trunk') { color = '#ea580c'; width = 5; }
          else if (hw === 'primary') { color = '#f59e0b'; width = 4; }
          else if (hw === 'secondary') { color = '#eab308'; width = 3; }
          else if (hw === 'tertiary') { color = '#a3a3a3'; width = 2; }
          return {
            type: 'Feature',
            properties: {
              name: f.properties.name || '',
              highway: hw,
              color, width,
            },
            geometry: f.geometry,
          };
        }),
      };

      this.roadSource = await GeoJsonDataSource.load(fc, {
        stroke: Color.WHITE, strokeWidth: 1,
      });

      this.roadSource.entities.values.forEach((e: any) => {
        if (e.polyline) {
          const props = e.properties;
          const c = props ? props['color']?.getValue() : null;
          const w = props ? props['width']?.getValue() : null;
          const nm = props ? props['name']?.getValue() : null;
          if (c) e.polyline.material = new ColorMaterialProperty(Color.fromCssColorString(c));
          if (w) e.polyline.width = w;
          if (nm && nm !== '') {
            e.label = {
              text: nm,
              font: '700 12px system-ui',
              style: LabelStyle.FILL_AND_OUTLINE,
              outlineWidth: 3,
              outlineColor: Color.WHITE,
              fillColor: Color.fromCssColorString('#7c2d12'),
              verticalOrigin: VerticalOrigin.CENTER,
              scaleByDistance: new NearFarScalar(10, 1.2, 500000, 0.6),
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
              showBackground: true,
              backgroundColor: Color.WHITE.withAlpha(0.7),
              backgroundPadding: new Cartesian2(5, 3),
            };
          }
        }
      });

      await this.viewer!.dataSources.add(this.roadSource);
      this.roadCount = fc.features.length;
      this.statusMessage = this.roadCount + ' roads in view';
    } catch (err) {
      console.error(err);
      this.statusMessage = 'Roads failed';
    }
    this.cdr.detectChanges();
  }

  async toggleFacilities() {
    this.showFacilities = !this.showFacilities;
    if (!this.showFacilities) {
      if (this.facilitySource) { this.viewer!.dataSources.remove(this.facilitySource, true); this.facilitySource = undefined; }
      this.facilityCount = 0;
      this.cdr.detectChanges();
      return;
    }
    try {
      const countyName = this.selectedCounty?.name;
      const facs = await this.api.getFacilities(countyName);  // all types, filter client-side
      const fc = {
        type: 'FeatureCollection',
        features: facs.map(f => ({
          type: 'Feature',
          properties: { name: f.name, type: f.type, county: f.county },
          geometry: { type: 'Point', coordinates: [f.longitude, f.latitude] }
        }))
      };
      this.facilitySource = await GeoJsonDataSource.load(fc, {
        markerColor: Color.RED, markerSize: 32,
      });
      this.facilitySource.entities.values.forEach((e: any) => {
        if (e.point) {
          const props = e.properties;
          const name = props ? props['name']?.getValue() : null;
          const type = props ? props['type']?.getValue() : null;
          let c = Color.fromCssColorString('#dc2626');
          if (type === 'school') c = Color.fromCssColorString('#2563eb');
          else if (type === 'police') c = Color.fromCssColorString('#7c3aed');
          else if (type === 'fire') c = Color.fromCssColorString('#f59e0b');
          e.point.color = new ColorMaterialProperty(c);
          e.point.pixelSize = 12;
          e.point.outlineColor = new ColorMaterialProperty(Color.WHITE);
          e.point.outlineWidth = 2;
          e.point.disableDepthTestDistance = Number.POSITIVE_INFINITY;
          if (name) {
            const icon = type === 'hospital' ? '🏥' : type === 'school' ? '🎓' : type === 'police' ? '🚔' : type === 'fire' ? '🚒' : '📍';
            e.label = {
              text: icon + ' ' + name,
              font: '700 13px system-ui, sans-serif',
              style: LabelStyle.FILL_AND_OUTLINE,
              outlineWidth: 3,
              outlineColor: Color.WHITE,
              fillColor: Color.fromCssColorString('#111827'),
              verticalOrigin: VerticalOrigin.BOTTOM,
              pixelOffset: new Cartesian2(0, -20),
              scaleByDistance: new NearFarScalar(10, 1.1, 500000, 0.6),
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
              showBackground: true,
              backgroundColor: Color.WHITE.withAlpha(0.7),
              backgroundPadding: new Cartesian2(6, 3),
            };
          }
        }
      });
      await this.viewer!.dataSources.add(this.facilitySource);
      this.facilityCount = facs.length;
      this.statusMessage = this.facilityCount + ' facilities in ' + (countyName || 'Kenya');
    } catch (err) { console.error(err); this.statusMessage = 'Facilities failed'; }
    this.cdr.detectChanges();
  }

  async toggleSublocations() {
    this.showSublocations = !this.showSublocations;
    if (!this.showSublocations) {
      if (this.sublocationSource) { this.viewer!.dataSources.remove(this.sublocationSource, true); this.sublocationSource = undefined; }
      this.sublocationCount = 0;
      this.cdr.detectChanges();
      return;
    }
    try {
      this.statusMessage = 'Loading sub-counties...';
      this.cdr.detectChanges();
      const countyName = this.selectedCounty?.name;
      const subs = await this.api.getSublocations(countyName);
      this.sublocationSource = await GeoJsonDataSource.load(subs, {
        stroke: Color.fromCssColorString('#1e40af'),
        strokeWidth: 2,
        fill: Color.TRANSPARENT,
      });
      this.sublocationSource.entities.values.forEach((e: any) => {
        if (e.polygon) {
          const props = e.properties;
          const name = props ? props['name']?.getValue() : null;
          if (name) {
            e.label = {
              text: name,
              font: '700 13px system-ui',
              style: LabelStyle.FILL_AND_OUTLINE,
              outlineWidth: 4,
              outlineColor: Color.WHITE,
              fillColor: Color.fromCssColorString('#1e3a8a'),
              verticalOrigin: VerticalOrigin.CENTER,
              heightReference: HeightReference.CLAMP_TO_GROUND,
              scaleByDistance: new NearFarScalar(10, 1.0, 5000000, 0.5),
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
            };
          }
        }
      });
      await this.viewer!.dataSources.add(this.sublocationSource);
      this.sublocationCount = subs.features.length;
      this.statusMessage = this.sublocationCount + ' sub-counties in ' + (countyName || 'Kenya');
    } catch (err) { console.error(err); this.statusMessage = 'Sub-counties failed'; }
    this.cdr.detectChanges();
  }

  toggleMeasure() { this.measureMode = !this.measureMode; this.measurePoints = []; this.measureResult = ''; this.cdr.detectChanges(); }
  clearMeasure() { this.measurePoints = []; this.measureResult = ''; this.cdr.detectChanges(); }

  toggleCompareMode() { this.compareMode = !this.compareMode; this.compareCounty = null; this.compareResult = null; this.cdr.detectChanges(); }
  private runComparison() {
    const a = this.selectedCounty; const b = this.compareCounty;
    if (!a || !b) return;
    this.compareResult = {
      popRatio: b.population ? ((a.population ?? 0) / b.population).toFixed(2) : '—',
      areaRatio: b.area_km2 ? ((a.area_km2 ?? 0) / b.area_km2).toFixed(2) : '—',
      densityA: a.area_km2 ? ((a.population ?? 0) / a.area_km2).toFixed(1) : '—',
      densityB: b.area_km2 ? ((b.population ?? 0) / b.area_km2).toFixed(1) : '—',
    };
  }
  clearComparison() { this.compareCounty = null; this.compareResult = null; this.cdr.detectChanges(); }

  toggleNearestMode() { this.nearestMode = !this.nearestMode; this.nearestResult = null; this.cdr.detectChanges(); }
  private async findNearest(lat: number, lon: number) {
    try {
      this.nearestResult = await this.api.getNearestFacility(lat, lon, 'hospital');
      this.statusMessage = this.nearestResult.error ? 'No hospitals' : `Nearest: ${this.nearestResult.name} (${this.nearestResult.distance_km} km)`;
    } catch { this.statusMessage = 'Nearest failed'; }
    this.cdr.detectChanges();
  }

  togglePinMode() { this.pinMode = !this.pinMode; this.statusMessage = this.pinMode ? 'Pin: click anywhere' : 'Ready'; this.cdr.detectChanges(); }
  private async dropPin(lon: number, lat: number) {
    this.pins.push({ lon, lat, label: `Pin ${this.pins.length + 1}` });
    await this.refreshPins();
    this.cdr.detectChanges();
  }
  async clearPins() {
    this.pins = [];
    if (this.pinDataSource) { this.viewer!.dataSources.remove(this.pinDataSource, true); this.pinDataSource = undefined; }
    this.cdr.detectChanges();
  }
  private async refreshPins() {
    if (this.pinDataSource) this.viewer!.dataSources.remove(this.pinDataSource, true);
    const fc = {
      type: 'FeatureCollection',
      features: this.pins.map((p, i) => ({
        type: 'Feature',
        properties: { name: p.label, index: i + 1 },
        geometry: { type: 'Point', coordinates: [p.lon, p.lat] }
      }))
    };
    this.pinDataSource = await GeoJsonDataSource.load(fc, {
      markerColor: Color.fromCssColorString('#e91e63'), markerSize: 36,
    });
    await this.viewer!.dataSources.add(this.pinDataSource);
  }

  exportVisible() {
    if (!this.boundaryDataSource) return;
    const features: any[] = [];
    this.boundaryDataSource.entities.values.forEach((e: any) => {
      if (e.polygon) {
        const props = e.properties;
        const name = props ? props['name']?.getValue() : null;
        if (name) features.push({ type: 'Feature', properties: { name } });
      }
    });
    const blob = new Blob([JSON.stringify({ exported: new Date().toISOString(), counties: features }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'terratwin-export.json'; a.click();
    URL.revokeObjectURL(url);
    this.statusMessage = 'Exported';
    this.cdr.detectChanges();
  }

  takeScreenshot() {
    if (!this.viewer) return;
    this.viewer.render();
    this.viewer.canvas.toBlob((blob) => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `terratwin-${Date.now()}.png`; a.click();
      URL.revokeObjectURL(url);
    });
    this.statusMessage = 'Screenshot saved';
    this.cdr.detectChanges();
  }

  togglePresentationMode() {
    this.presentationMode = !this.presentationMode;
    this.sidebarOpen = !this.presentationMode;
    this.cdr.detectChanges();
  }

  goHome() { if (this.boundaryDataSource) this.viewer!.zoomTo(this.boundaryDataSource); }
  toggleSidebar() { this.state.toggleSidebar(); }
  toggleTheme() { this.state.toggleTheme(); }

  clearSelection() {
    this.selectedCounty = null;
    this.countyStats = null;
    this.facilities = [];
    this.featureInfo = null;
    this.highlightEntity(null);
    if (this.roadSource) { this.viewer!.dataSources.remove(this.roadSource, true); this.roadSource = undefined; this.showRoads = false; this.roadCount = 0; }
    if (this.facilitySource) { this.viewer!.dataSources.remove(this.facilitySource, true); this.facilitySource = undefined; this.showFacilities = false; this.facilityCount = 0; }
    if (this.sublocationSource) { this.viewer!.dataSources.remove(this.sublocationSource, true); this.sublocationSource = undefined; this.showSublocations = false; this.sublocationCount = 0; }
    this.cdr.detectChanges();
  }

  shareLink() {
    const params = new URLSearchParams();
    if (this.selectedCounty) params.set('county', this.selectedCounty.name);
    const url = window.location.origin + window.location.pathname + '?' + params.toString();
    navigator.clipboard.writeText(url);
    this.statusMessage = 'Link copied';
    this.cdr.detectChanges();
  }

  formatNumber(n: number | undefined): string {
    if (n === undefined || n === null) return '—';
    return n.toLocaleString();
  }

  ngOnDestroy() {
    this.handler?.destroy();
    this.viewer?.destroy();
  }
}
