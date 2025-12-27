/**
 * Weather App - Location & UI Management
 */

// DOM Elements
const elements = {
  loadingState: document.getElementById('loading-state'),
  permissionState: document.getElementById('permission-state'),
  weatherState: document.getElementById('weather-state'),
  loadingText: document.getElementById('loading-text'),
  grantLocationBtn: document.getElementById('grant-location'),
  permissionError: document.getElementById('permission-error'),
  toggleLocationBtn: document.getElementById('toggle-location'),
  locationModal: document.getElementById('location-modal'),
  closeModalBtn: document.getElementById('close-modal'),
  modalBackdrop: document.getElementById('modal-backdrop'),
  useCurrentLocationBtn: document.getElementById('use-current-location'),
  switchLocationModal: document.getElementById('switch-location-modal'),
  switchModalBackdrop: document.getElementById('switch-modal-backdrop'),
  switchToCurrentBtn: document.getElementById('switch-to-current'),
  keepLocationBtn: document.getElementById('keep-location'),
  addressInput: document.getElementById('address'),
  refreshBtn: document.getElementById('refresh-weather'),
  refreshModal: document.getElementById('refresh-modal'),
  refreshModalBackdrop: document.getElementById('refresh-modal-backdrop'),
  refreshCloseBtn: document.getElementById('refresh-close'),
  refreshLocationList: document.getElementById('refresh-location-list'),
  refreshStatus: document.getElementById('refresh-status'),
};

// Configuration
const CONFIG = {
  LOCATION_DELTA_THRESHOLD: 0.03,
  GEOLOCATION_OPTIONS: {
    enableHighAccuracy: false,
    timeout: 10000,
    maximumAge: 60000,
  },
};

// State
let pendingSwitchLocation = null;

/**
 * Show a specific UI state and hide others
 */
function showState(state) {
  elements.loadingState?.classList.add('hidden');
  elements.permissionState?.classList.add('hidden');
  elements.weatherState?.classList.add('hidden');
  state?.classList.remove('hidden');
}

/**
 * Open the location search modal
 */
function openModal() {
  elements.locationModal?.classList.remove('hidden');
  elements.addressInput?.focus();
}

/**
 * Close the location search modal
 */
function closeModal() {
  elements.locationModal?.classList.add('hidden');
}

/**
 * Open the switch location modal
 */
function openSwitchModal(coords) {
  pendingSwitchLocation = coords;
  elements.switchLocationModal?.classList.remove('hidden');
}

/**
 * Close the switch location modal
 */
function closeSwitchModal() {
  elements.switchLocationModal?.classList.add('hidden');
  pendingSwitchLocation = null;
}

/**
 * Get a cookie value by name
 */
function getCookieValue(name) {
  const match = document.cookie.split('; ').find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split('=')[1]) : null;
}

/**
 * Get cached location from cookies
 */
function getCachedLocation() {
  const lat = Number.parseFloat(getCookieValue('last_lat'));
  const lon = Number.parseFloat(getCookieValue('last_lon'));
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return null;
  }
  return { lat, lon };
}

/**
 * Check if two locations are significantly different
 */
function isSignificantlyDifferent(a, b) {
  return (
    Math.abs(a.lat - b.lat) > CONFIG.LOCATION_DELTA_THRESHOLD ||
    Math.abs(a.lon - b.lon) > CONFIG.LOCATION_DELTA_THRESHOLD
  );
}

/**
 * Redirect to a location
 */
function redirectToLocation(coords) {
  const latValue = Number(coords.latitude ?? coords.lat);
  const lonValue = Number(coords.longitude ?? coords.lon);
  if (!Number.isFinite(latValue) || !Number.isFinite(lonValue)) {
    return;
  }
  const lat = latValue.toFixed(4);
  const lon = lonValue.toFixed(4);
  window.location = `/?lat=${lat}&lon=${lon}`;
}

/**
 * Request user's location
 */
function requestLocation({ showLoading = true, onSuccess } = {}) {
  if (showLoading) {
    showState(elements.loadingState);
    if (elements.loadingText) {
      elements.loadingText.textContent = 'Detecting your location...';
    }
  }

  const handleSuccess = onSuccess || ((coords) => redirectToLocation(coords));

  navigator.geolocation.getCurrentPosition(
    (position) => {
      if (showLoading && elements.loadingText) {
        elements.loadingText.textContent = 'Loading weather...';
      }
      handleSuccess(position.coords);
    },
    (error) => {
      if (!showLoading) return;
      
      if (error.code === error.PERMISSION_DENIED) {
        showState(elements.permissionState);
      } else {
        if (elements.permissionError) {
          elements.permissionError.textContent = error.message || 'Unable to get location';
          elements.permissionError.classList.remove('hidden');
        }
        showState(elements.permissionState);
      }
    },
    CONFIG.GEOLOCATION_OPTIONS
  );
}

/**
 * Open the refresh cache modal
 */
function openRefreshModal() {
  elements.refreshModal?.classList.remove('hidden');
  elements.refreshStatus?.classList.add('hidden');
}

/**
 * Close the refresh cache modal
 */
function closeRefreshModal() {
  elements.refreshModal?.classList.add('hidden');
  elements.refreshStatus?.classList.add('hidden');
}

/**
 * Handle refresh/delete actions for a location
 */
async function handleRefreshAction(action, locationKey) {
  if (!locationKey) return;
  const isDelete = action === 'delete';

  closeRefreshModal();
  if (elements.loadingText) {
    elements.loadingText.textContent = isDelete
      ? 'Removing cached data...'
      : 'Refreshing weather data...';
  }
  showState(elements.loadingState);

  try {
    const response = await fetch('/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, location_key: locationKey }),
    });
    if (!response.ok) {
      throw new Error('Refresh failed');
    }
  } catch (error) {
    showState(elements.weatherState);
    openRefreshModal();
    if (elements.refreshStatus) {
      elements.refreshStatus.textContent = 'Unable to update cache. Please try again.';
      elements.refreshStatus.classList.remove('hidden');
    }
    return;
  }

  window.location.reload();
}

/**
 * Check if user has moved and offer to switch location
 */
function checkForLocationSwitch(coords) {
  const cached = getCachedLocation();
  if (!cached) return;
  
  const fresh = { lat: coords.latitude, lon: coords.longitude };
  if (isSignificantlyDifferent(cached, fresh)) {
    openSwitchModal(fresh);
  }
}

/**
 * Initialize the application
 */
function initWeatherApp(options = {}) {
  const { hasWeatherData, usedCachedLocation, hasLocationParams } = options;

  // Initial load logic
  if (!hasWeatherData && !hasLocationParams) {
    if (!navigator.geolocation) {
      showState(elements.permissionState);
      if (elements.permissionError) {
        elements.permissionError.textContent = 'Geolocation is not supported';
        elements.permissionError.classList.remove('hidden');
      }
    } else {
      requestLocation();
    }
  } else if (usedCachedLocation && navigator.geolocation) {
    requestLocation({ showLoading: false, onSuccess: checkForLocationSwitch });
  }

  // Event Listeners
  elements.grantLocationBtn?.addEventListener('click', () => {
    elements.permissionError?.classList.add('hidden');
    requestLocation();
  });

  elements.toggleLocationBtn?.addEventListener('click', openModal);
  elements.closeModalBtn?.addEventListener('click', closeModal);
  elements.modalBackdrop?.addEventListener('click', closeModal);

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!elements.locationModal?.classList.contains('hidden')) {
      closeModal();
    }
    if (!elements.switchLocationModal?.classList.contains('hidden')) {
      closeSwitchModal();
    }
    if (!elements.refreshModal?.classList.contains('hidden')) {
      closeRefreshModal();
    }
  });

  elements.useCurrentLocationBtn?.addEventListener('click', () => {
    closeModal();
    requestLocation();
  });

  elements.switchToCurrentBtn?.addEventListener('click', () => {
    if (!pendingSwitchLocation) return;
    const coords = pendingSwitchLocation;
    closeSwitchModal();
    redirectToLocation(coords);
  });

  elements.keepLocationBtn?.addEventListener('click', closeSwitchModal);
  elements.switchModalBackdrop?.addEventListener('click', closeSwitchModal);

  elements.refreshBtn?.addEventListener('click', openRefreshModal);
  elements.refreshModalBackdrop?.addEventListener('click', closeRefreshModal);
  elements.refreshCloseBtn?.addEventListener('click', closeRefreshModal);

  elements.refreshLocationList?.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-refresh-action]');
    if (!button) return;
    const action = button.dataset.refreshAction;
    const locationKey = button.dataset.locationKey;
    handleRefreshAction(action, locationKey);
  });
}

/**
 * Determine weather theme based on forecast text
 */
function getWeatherTheme(shortForecast, isDaytime = true) {
  if (!shortForecast) return null;
  
  const forecast = shortForecast.toLowerCase();
  
  // Check for specific weather conditions (order matters - more specific first)
  if (forecast.includes('thunder') || forecast.includes('storm')) {
    return 'storm';
  }
  if (forecast.includes('snow') || forecast.includes('blizzard') || forecast.includes('flurr')) {
    return 'snow';
  }
  if (forecast.includes('rain') || forecast.includes('shower') || forecast.includes('drizzle')) {
    return 'rain';
  }
  if (forecast.includes('fog') || forecast.includes('mist') || forecast.includes('haze') || forecast.includes('smoke')) {
    return 'fog';
  }
  if (forecast.includes('wind') && !forecast.includes('sun') && !forecast.includes('clear')) {
    return 'wind';
  }
  if (forecast.includes('cloud') || forecast.includes('overcast')) {
    return 'cloudy';
  }
  if (forecast.includes('hot') || forecast.includes('heat')) {
    return 'hot';
  }
  if (forecast.includes('sun') || forecast.includes('clear') || forecast.includes('fair')) {
    return isDaytime ? 'clear' : 'night';
  }
  
  // Default based on time of day
  return isDaytime ? null : 'night';
}

/**
 * Create weather animation particles
 */
function createWeatherEffects(theme) {
  const container = document.getElementById('weather-effects');
  if (!container) return;
  
  // Clear existing effects
  container.innerHTML = '';
  
  // Check for reduced motion preference
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }
  
  switch (theme) {
    case 'rain':
    case 'storm':
      createRainEffect(container, theme === 'storm');
      break;
    case 'snow':
      createSnowEffect(container);
      break;
    case 'fog':
      createFogEffect(container);
      break;
    case 'clear':
      createSunEffect(container);
      break;
    case 'night':
      createStarsEffect(container);
      break;
    case 'wind':
      createWindEffect(container);
      break;
    case 'hot':
      createHeatEffect(container);
      break;
  }
}

function createRainEffect(container, isStorm) {
  const dropCount = isStorm ? 120 : 80;
  
  for (let i = 0; i < dropCount; i++) {
    const drop = document.createElement('div');
    drop.className = 'weather-particle rain-drop';
    drop.style.left = `${Math.random() * 100}%`;
    drop.style.animationDuration = `${0.4 + Math.random() * 0.4}s`;
    drop.style.animationDelay = `${Math.random() * 2}s`;
    drop.style.opacity = 0.5 + Math.random() * 0.5;
    // Vary the height for depth perception
    const scale = 0.5 + Math.random() * 0.5;
    drop.style.transform = `scaleY(${scale})`;
    container.appendChild(drop);
  }
  
  // Add rain mist at the bottom
  const mist = document.createElement('div');
  mist.className = 'weather-particle rain-mist';
  container.appendChild(mist);
  
  if (isStorm) {
    // Add multiple lightning flashes with different timings
    for (let i = 0; i < 2; i++) {
      const flash = document.createElement('div');
      flash.className = 'lightning-flash';
      flash.style.animationDelay = `${i * 3 + Math.random() * 2}s`;
      container.appendChild(flash);
    }
  }
}

function createSnowEffect(container) {
  const flakeCount = 40;
  
  for (let i = 0; i < flakeCount; i++) {
    const flake = document.createElement('div');
    flake.className = 'weather-particle snowflake';
    flake.style.left = `${Math.random() * 100}%`;
    flake.style.width = `${4 + Math.random() * 6}px`;
    flake.style.height = flake.style.width;
    flake.style.animationDuration = `${5 + Math.random() * 10}s`;
    flake.style.animationDelay = `${Math.random() * 5}s`;
    flake.style.opacity = 0.4 + Math.random() * 0.4;
    container.appendChild(flake);
  }
}

function createFogEffect(container) {
  for (let i = 0; i < 3; i++) {
    const fog = document.createElement('div');
    fog.className = 'weather-particle fog-layer';
    container.appendChild(fog);
  }
}

function createSunEffect(container) {
  // Add sun glow
  const glow = document.createElement('div');
  glow.className = 'weather-particle sun-glow';
  container.appendChild(glow);
  
  // Add sun rays
  for (let i = 0; i < 3; i++) {
    const ray = document.createElement('div');
    ray.className = 'weather-particle sun-ray';
    container.appendChild(ray);
  }
}

function createStarsEffect(container) {
  // Add moon glow
  const moon = document.createElement('div');
  moon.className = 'weather-particle moon-glow';
  container.appendChild(moon);
  
  // Regular stars
  const starCount = 80;
  for (let i = 0; i < starCount; i++) {
    const star = document.createElement('div');
    star.className = 'weather-particle star';
    // Make some stars brighter
    if (Math.random() > 0.85) {
      star.classList.add('bright');
    }
    star.style.left = `${Math.random() * 100}%`;
    star.style.top = `${Math.random() * 70}%`;
    star.style.animationDuration = `${2 + Math.random() * 4}s`;
    star.style.animationDelay = `${Math.random() * 4}s`;
    container.appendChild(star);
  }
  
  // Shooting stars
  for (let i = 0; i < 3; i++) {
    const shootingStar = document.createElement('div');
    shootingStar.className = 'weather-particle shooting-star';
    shootingStar.style.left = `${20 + Math.random() * 40}%`;
    shootingStar.style.top = `${5 + Math.random() * 20}%`;
    shootingStar.style.animationDelay = `${i * 4 + Math.random() * 3}s`;
    shootingStar.style.animationDuration = `${2.5 + Math.random() * 1.5}s`;
    container.appendChild(shootingStar);
  }
}

function createWindEffect(container) {
  const streakCount = 15;
  
  for (let i = 0; i < streakCount; i++) {
    const streak = document.createElement('div');
    streak.className = 'weather-particle wind-streak';
    streak.style.top = `${10 + Math.random() * 80}%`;
    streak.style.width = `${50 + Math.random() * 150}px`;
    streak.style.animationDuration = `${1 + Math.random() * 2}s`;
    streak.style.animationDelay = `${Math.random() * 3}s`;
    container.appendChild(streak);
  }
}

function createHeatEffect(container) {
  const wave = document.createElement('div');
  wave.className = 'weather-particle heat-wave';
  container.appendChild(wave);
}

/**
 * Apply weather-based background theme
 */
function applyWeatherTheme(shortForecast, isDaytime = true) {
  const theme = getWeatherTheme(shortForecast, isDaytime);
  if (theme) {
    document.body.setAttribute('data-weather', theme);
    createWeatherEffects(theme);
  } else {
    document.body.removeAttribute('data-weather');
    const container = document.getElementById('weather-effects');
    if (container) container.innerHTML = '';
  }
}

// Export for use in templates
window.WeatherApp = {
  init: initWeatherApp,
  showState,
  openModal,
  closeModal,
  requestLocation,
  applyWeatherTheme,
  getWeatherTheme,
};
