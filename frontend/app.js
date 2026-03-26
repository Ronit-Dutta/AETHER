/* ================================================================
   PROJECT AETHER - Main Application Engine
   Three.js 3D Planet Rendering + Supabase Data Layer
   ================================================================ */

// --- Supabase Configuration --- 
const SUPABASE_URL = 'https://ikiuqbraocimoozeaioy.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlraXVxYnJhb2NpbW9vemVhaW95Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyNTkyNTMsImV4cCI6MjA4OTgzNTI1M30.aJuvmbZTlEy4LIy2I_O4N2ETX7hMF6WXLKiDUhmDk4E';

let supabase = null;

// --- Global State --- 
let allPlanets = [];
let currentFilter = 'all';
let viewerScene, viewerCamera, viewerRenderer, viewerPlanetMesh;
let viewerAnimationId;
let viewerAutoRotate = true;
let cardScenes = {};

// --- Star Field Generator --- 
function generateStars() {
    const container = document.getElementById('starsContainer');
    if (!container) return;
    const count = 150;
    for (let i = 0; i < count; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        star.style.left = Math.random() * 100 + '%';
        star.style.top = Math.random() * 100 + '%';
        star.style.setProperty('--dur', (2 + Math.random() * 4) + 's');
        star.style.setProperty('--delay', Math.random() * 5 + 's');
        star.style.setProperty('--opacity', (0.2 + Math.random() * 0.6).toString());
        const size = Math.random() < 0.1 ? 3 : (Math.random() < 0.3 ? 2 : 1);
        star.style.width = size + 'px';
        star.style.height = size + 'px';
        container.appendChild(star);
    }
}

// --- Planet Color Palette based on Temperature --- 
function getPlanetColors(tempK, planetType) {
    if (!tempK) tempK = 300;
    const t = parseFloat(tempK);

    // Gas Giants get special treatment
    if (planetType === 'Gas Giant' || planetType === 'Super-Jupiter') {
        return {
            base: new THREE.Color(0.7, 0.55, 0.3),
            accent: new THREE.Color(0.85, 0.65, 0.35),
            atmosphere: new THREE.Color(0.9, 0.7, 0.4),
            glow: 0xd4a43a,
            emissive: new THREE.Color(0.05, 0.03, 0.0)
        };
    }
    if (planetType === 'Neptune-like' || planetType === 'Mini-Neptune') {
        return {
            base: new THREE.Color(0.2, 0.4, 0.7),
            accent: new THREE.Color(0.3, 0.5, 0.85),
            atmosphere: new THREE.Color(0.4, 0.6, 0.9),
            glow: 0x4488cc,
            emissive: new THREE.Color(0.02, 0.03, 0.06)
        };
    }

    // Rocky planets based on temperature
    if (t > 1000) {
        return {
            base: new THREE.Color(0.9, 0.2, 0.05),
            accent: new THREE.Color(1.0, 0.5, 0.1),
            atmosphere: new THREE.Color(1.0, 0.3, 0.1),
            glow: 0xff4400,
            emissive: new THREE.Color(0.2, 0.05, 0.0)
        };
    } else if (t > 600) {
        return {
            base: new THREE.Color(0.75, 0.3, 0.1),
            accent: new THREE.Color(0.9, 0.45, 0.15),
            atmosphere: new THREE.Color(0.85, 0.4, 0.15),
            glow: 0xcc5500,
            emissive: new THREE.Color(0.1, 0.03, 0.0)
        };
    } else if (t > 350) {
        return {
            base: new THREE.Color(0.6, 0.45, 0.25),
            accent: new THREE.Color(0.7, 0.55, 0.3),
            atmosphere: new THREE.Color(0.7, 0.5, 0.25),
            glow: 0xaa7733,
            emissive: new THREE.Color(0.03, 0.02, 0.0)
        };
    } else if (t > 230) {
        // Temperate / Earth-like
        return {
            base: new THREE.Color(0.15, 0.45, 0.3),
            accent: new THREE.Color(0.2, 0.5, 0.7),
            atmosphere: new THREE.Color(0.3, 0.6, 0.9),
            glow: 0x2299cc,
            emissive: new THREE.Color(0.01, 0.02, 0.03)
        };
    } else if (t > 150) {
        // Cold world
        return {
            base: new THREE.Color(0.5, 0.6, 0.7),
            accent: new THREE.Color(0.6, 0.7, 0.8),
            atmosphere: new THREE.Color(0.6, 0.7, 0.85),
            glow: 0x7799bb,
            emissive: new THREE.Color(0.02, 0.03, 0.04)
        };
    } else {
        // Frozen / Ice world
        return {
            base: new THREE.Color(0.75, 0.85, 0.95),
            accent: new THREE.Color(0.85, 0.92, 1.0),
            atmosphere: new THREE.Color(0.8, 0.9, 1.0),
            glow: 0xaaccff,
            emissive: new THREE.Color(0.03, 0.04, 0.06)
        };
    }
}

// --- Procedural Planet Texture Generation --- 
function generatePlanetTexture(width, height, colors, planetType, seed) {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    // Simple pseudo-random from seed
    let s = seed || Math.random() * 10000;
    function seededRandom() {
        s = (s * 9301 + 49297) % 233280;
        return s / 233280;
    }

    // Fill base color
    ctx.fillStyle = `rgb(${Math.floor(colors.base.r*255)}, ${Math.floor(colors.base.g*255)}, ${Math.floor(colors.base.b*255)})`;
    ctx.fillRect(0, 0, width, height);

    // Generate noise-like terrain
    const isGasGiant = planetType === 'Gas Giant' || planetType === 'Super-Jupiter' || 
                       planetType === 'Neptune-like' || planetType === 'Mini-Neptune';

    if (isGasGiant) {
        // Horizontal bands for gas giants
        for (let y = 0; y < height; y++) {
            const bandIntensity = Math.sin(y * 0.05 + seededRandom() * 2) * 0.5 + 0.5;
            const turb = Math.sin(y * 0.02) * Math.cos(y * 0.08 + seededRandom()) * 15;
            const r = Math.floor(colors.base.r * 255 * (0.7 + bandIntensity * 0.3));
            const g = Math.floor(colors.base.g * 255 * (0.7 + bandIntensity * 0.4));
            const b = Math.floor(colors.base.b * 255 * (0.7 + bandIntensity * 0.3));
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.5)`;
            ctx.fillRect(0 + turb, y, width, 1);
        }
        // Storm spots
        for (let i = 0; i < 3; i++) {
            const sx = seededRandom() * width;
            const sy = seededRandom() * height;
            const sr = 10 + seededRandom() * 20;
            const grad = ctx.createRadialGradient(sx, sy, 0, sx, sy, sr);
            grad.addColorStop(0, `rgba(${Math.floor(colors.accent.r*255)}, ${Math.floor(colors.accent.g*255)}, ${Math.floor(colors.accent.b*255)}, 0.6)`);
            grad.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.ellipse(sx, sy, sr * 1.5, sr, 0, 0, Math.PI * 2);
            ctx.fill();
        }
    } else {
        // Terrain patches for rocky worlds
        for (let i = 0; i < 80; i++) {
            const px = seededRandom() * width;
            const py = seededRandom() * height;
            const pr = 5 + seededRandom() * 40;
            const c = seededRandom() > 0.5 ? colors.accent : colors.base;
            const alpha = 0.1 + seededRandom() * 0.4;
            const grad = ctx.createRadialGradient(px, py, 0, px, py, pr);
            grad.addColorStop(0, `rgba(${Math.floor(c.r*255)}, ${Math.floor(c.g*255)}, ${Math.floor(c.b*255)}, ${alpha})`);
            grad.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(px, py, pr, 0, Math.PI * 2);
            ctx.fill();
        }

        // Ice caps for cold worlds
        if (colors.base.r > 0.5 && colors.base.b > 0.8) {
            const capGrad = ctx.createLinearGradient(0, 0, 0, height);
            capGrad.addColorStop(0, 'rgba(220, 235, 255, 0.7)');
            capGrad.addColorStop(0.15, 'rgba(220, 235, 255, 0)');
            capGrad.addColorStop(0.85, 'rgba(220, 235, 255, 0)');
            capGrad.addColorStop(1, 'rgba(220, 235, 255, 0.7)');
            ctx.fillStyle = capGrad;
            ctx.fillRect(0, 0, width, height);
        }
    }

    return new THREE.CanvasTexture(canvas);
}

// --- Create 3D Planet Mesh ---
function createPlanetMesh(planetData, size) {
    const temp = planetData.equilibrium_temp_k || planetData.pl_eqt;
    const type = planetData.planet_type || 'Unknown';
    const colors = getPlanetColors(temp, type);
    
    // Planet sphere
    const geometry = new THREE.SphereGeometry(size, 64, 64);
    const texture = generatePlanetTexture(512, 256, colors, type, 
        planetData.pl_name ? planetData.pl_name.charCodeAt(0) * 1000 : Math.random() * 10000);
    
    const material = new THREE.MeshPhongMaterial({
        map: texture,
        emissive: colors.emissive,
        emissiveIntensity: 0.3,
        shininess: 15,
        bumpScale: 0.02,
    });

    const planet = new THREE.Mesh(geometry, material);

    // Atmosphere glow
    const atmosGeometry = new THREE.SphereGeometry(size * 1.03, 64, 64);
    const atmosMaterial = new THREE.MeshPhongMaterial({
        color: colors.atmosphere,
        transparent: true,
        opacity: 0.15,
        side: THREE.FrontSide,
    });
    const atmosphere = new THREE.Mesh(atmosGeometry, atmosMaterial);
    planet.add(atmosphere);

    // Outer glow ring
    const glowGeometry = new THREE.SphereGeometry(size * 1.12, 32, 32);
    const glowMaterial = new THREE.MeshBasicMaterial({
        color: colors.glow,
        transparent: true,
        opacity: 0.06,
        side: THREE.BackSide,
    });
    const glow = new THREE.Mesh(glowGeometry, glowMaterial);
    planet.add(glow);

    // Random axis tilt
    planet.rotation.z = (Math.random() - 0.5) * 0.4;

    return planet;
}

// --- Render a small 3D planet in a card canvas ---
function renderCardPlanet(containerId, planetData) {
    const container = document.getElementById(containerId);
    if (!container || cardScenes[containerId]) return;

    const width = container.clientWidth || 350;
    const height = container.clientHeight || 200;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.z = 3.5;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x334466, 0.5);
    scene.add(ambientLight);
    const starLight = new THREE.DirectionalLight(0xffffff, 1.2);
    starLight.position.set(3, 2, 4);
    scene.add(starLight);
    const rimLight = new THREE.DirectionalLight(0x4488cc, 0.3);
    rimLight.position.set(-3, -1, -2);
    scene.add(rimLight);

    const planet = createPlanetMesh(planetData, 1.2);
    scene.add(planet);

    function animate() {
        const id = requestAnimationFrame(animate);
        planet.rotation.y += 0.003;
        renderer.render(scene, camera);
        cardScenes[containerId] = { scene, camera, renderer, planet, animId: id };
    }
    animate();
}

// --- Full 3D Viewer ---
function initViewer() {
    const container = document.getElementById('viewerCanvasContainer');
    if (!container) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 500;

    viewerScene = new THREE.Scene();
    viewerCamera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    viewerCamera.position.z = 4;

    viewerRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    viewerRenderer.setSize(width, height);
    viewerRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    viewerRenderer.setClearColor(0x030712, 1);

    // Insert before controls
    const controls = container.querySelector('.viewer-controls');
    container.insertBefore(viewerRenderer.domElement, controls);

    // Lighting
    viewerScene.add(new THREE.AmbientLight(0x334466, 0.4));
    const mainLight = new THREE.DirectionalLight(0xffffff, 1.5);
    mainLight.position.set(5, 3, 5);
    viewerScene.add(mainLight);
    const backLight = new THREE.DirectionalLight(0x4488cc, 0.4);
    backLight.position.set(-5, -2, -3);
    viewerScene.add(backLight);

    // Background stars for viewer
    const starGeometry = new THREE.BufferGeometry();
    const starCount = 2000;
    const positions = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i++) {
        positions[i] = (Math.random() - 0.5) * 200;
    }
    starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const starMaterial = new THREE.PointsMaterial({ color: 0xffffff, size: 0.15, transparent: true, opacity: 0.8 });
    viewerScene.add(new THREE.Points(starGeometry, starMaterial));

    function animateViewer() {
        viewerAnimationId = requestAnimationFrame(animateViewer);
        if (viewerPlanetMesh && viewerAutoRotate) {
            viewerPlanetMesh.rotation.y += 0.002;
        }
        viewerRenderer.render(viewerScene, viewerCamera);
    }
    animateViewer();

    // Mouse interaction (simple orbit)
    let isDragging = false, prevX = 0, prevY = 0;
    viewerRenderer.domElement.addEventListener('mousedown', (e) => { isDragging = true; prevX = e.clientX; prevY = e.clientY; });
    viewerRenderer.domElement.addEventListener('mousemove', (e) => {
        if (!isDragging || !viewerPlanetMesh) return;
        const dx = e.clientX - prevX;
        const dy = e.clientY - prevY;
        viewerPlanetMesh.rotation.y += dx * 0.005;
        viewerPlanetMesh.rotation.x += dy * 0.005;
        prevX = e.clientX;
        prevY = e.clientY;
    });
    viewerRenderer.domElement.addEventListener('mouseup', () => isDragging = false);
    viewerRenderer.domElement.addEventListener('mouseleave', () => isDragging = false);

    // Scroll zoom
    viewerRenderer.domElement.addEventListener('wheel', (e) => {
        e.preventDefault();
        viewerCamera.position.z = Math.max(2, Math.min(10, viewerCamera.position.z + e.deltaY * 0.005));
    }, { passive: false });
}

function loadPlanetInViewer(planetData) {
    if (!viewerScene) initViewer();

    // Remove old planet
    if (viewerPlanetMesh) {
        viewerScene.remove(viewerPlanetMesh);
        viewerPlanetMesh.geometry.dispose();
        viewerPlanetMesh.material.dispose();
    }

    viewerPlanetMesh = createPlanetMesh(planetData, 1.8);
    viewerScene.add(viewerPlanetMesh);

    // Update sidebar active state
    document.querySelectorAll('.viewer-planet-item').forEach(el => el.classList.remove('active'));
    const activeItem = document.querySelector(`.viewer-planet-item[data-name="${planetData.pl_name}"]`);
    if (activeItem) activeItem.classList.add('active');
}

function setViewerMode(mode) {
    document.querySelectorAll('.viewer-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    if (mode === 'surface') {
        viewerCamera.position.z = 2.2;
    } else {
        viewerCamera.position.z = 4;
    }
}

function toggleViewerRotation() {
    viewerAutoRotate = !viewerAutoRotate;
    event.target.textContent = viewerAutoRotate ? '- Rotation' : '- Rotation';
}

// --- Timeout Utility --- 
function promiseWithTimeout(promise, ms) {
    const timeout = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Timeout')), ms)
    );
    return Promise.race([promise, timeout]);
}

// --- Data Fetching --- 
async function fetchPlanets() {
    if (!supabase) return getDemoData();

    try {
        const { data, error } = await promiseWithTimeout(
            supabase
                .from('planets')
                .select('*')
                .order('habitability_score', { ascending: false }),
            3000
        );

        if (error) throw error;
        if (data && data.length > 0) return data;
        return getDemoData();
    } catch (e) {
        console.warn('Supabase fetch failed, using demo data:', e);
        return getDemoData();
    }
}

async function fetchMissionLogs() {
    if (!supabase) return getDemoLogs();

    try {
        const { data, error } = await promiseWithTimeout(
            supabase
                .from('mission_logs')
                .select('*')
                .order('started_at', { ascending: false })
                .limit(20),
            3000
        );

        if (error) throw error;
        if (data && data.length > 0) return data;
        return getDemoLogs();
    } catch (e) {
        console.warn('Mission logs fetch failed, using demo:', e);
        return getDemoLogs();
    }
}

async function fetchResearchPapers() {
    if (!supabase) return [];

    try {
        const { data, error } = await promiseWithTimeout(
            supabase
                .from('research_papers')
                .select('*')
                .order('publication_year', { ascending: false }),
            3000
        );

        if (error) throw error;
        return data || [];
    } catch (e) {
        console.warn('Research fetch failed:', e);
        return [];
    }
}

// --- Demo Data (used before first real mission runs) --- 
function getDemoData() {
    return [
        { pl_name: "TRAPPIST-1 e", host_star: "TRAPPIST-1", planet_type: "Terrestrial", planet_type_icon: "--", equilibrium_temp_k: 251, radius_earth: 0.92, mass_earth: 0.692, habitability_score: 78, habitability_classification: "Prime Candidate", habitability_color: "#00ff88", orbital_distance_au: 0.029, distance_ly: 40.7, discovery_method: "Transit", discovery_year: 2017, star_spectral_type: "M8V", short_description: "A temperate Earth-sized world locked in eternal twilight around an ultracool red dwarf, where liquid water may pool along the terminator zone.", bio_report: { environment_summary: "Standing on TRAPPIST-1 e, you'd experience a surreal permanent sunset. The dim red star would dominate half the sky while the other half remains in perpetual darkness. Winds might howl across the terminator line.", atmosphere_analysis: "Given its Earth-like mass, it could retain a nitrogen-CO2 atmosphere with surface pressures near 1-2 bar. Water vapor may exist in the twilight band.", surface_conditions: "The dayside likely features rocky terrain with possible shallow seas near the substellar point. The nightside could be covered in thick glacial ice sheets.", hypothetical_lifeforms: [{ species_name: "Umbra crystallophyta", common_name: "Twilight Crystal Bloom", description: "A bioluminescent photosynthetic organism that thrives in the dim red light of the terminator zone. Its crystalline structures focus sparse photons for energy.", adaptation: "Crystalline light-focusing appendages", size: "5-15 cm clusters", energy_source: "Modified photosynthesis tuned to infrared" }, { species_name: "Thermocaudatus glacialis", common_name: "Ice Tunnel Serpent", description: "A long, segmented creature that burrows through the ice sheets on the nightside, feeding on chemosynthetic microbes near hydrothermal vents.", adaptation: "Antifreeze proteins and thermal sensing organs", size: "30-60 cm length", energy_source: "Chemosynthetic symbiosis" }, { species_name: "Aeroplanktos rubrum", common_name: "Red Drifter", description: "Microscopic aerial organisms that float in the upper atmosphere, absorbing infrared radiation from the star for energy.", adaptation: "Light gas-filled vesicles for atmospheric buoyancy", size: "Microscopic, 0.1-0.5 mm", energy_source: "Infrared radiation harvesting" }], habitability_assessment: "TRAPPIST-1 e is one of the most promising candidates for habitability in the known exoplanet catalog. It sits squarely within its star's habitable zone with an Earth-like size. The main concern is tidal locking and stellar flares, but a robust atmosphere could mitigate both.", mission_recommendation: "A probe should carry a high-resolution infrared spectrometer to analyze atmospheric composition and a thermal mapper to identify the liquid water boundary.", fun_fact: "The entire TRAPPIST-1 system could fit inside Mercury's orbit around our Sun!" } },
        { pl_name: "Kepler-442 b", host_star: "Kepler-442", planet_type: "Super-Earth", planet_type_icon: "--", equilibrium_temp_k: 233, radius_earth: 1.34, mass_earth: 2.36, habitability_score: 72, habitability_classification: "Promising", habitability_color: "#88ff00", orbital_distance_au: 0.409, distance_ly: 1206, discovery_method: "Transit", discovery_year: 2015, star_spectral_type: "K", short_description: "A super-Earth orbiting in the habitable zone of a quiet orange dwarf star, with conditions potentially suitable for liquid water.", bio_report: { environment_summary: "Kepler-442 b would feel heavier than Earth, with roughly 1.3g surface gravity. The sky would glow a warm amber-orange from its K-type star. Thick clouds may roll over vast continental plateaus.", atmosphere_analysis: "Its larger size suggests it can retain a denser atmosphere than Earth, possibly 2-3 bar with significant water vapor, nitrogen, and CO2.", surface_conditions: "Likely a mix of deep oceans and mountainous continents. Higher gravity would create flatter terrain with broader, shallower seas.", hypothetical_lifeforms: [{ species_name: "Gravipodus fortis", common_name: "Boulder Walker", description: "A squat, heavily built hexapod adapted to the high gravity. It grazes on mineral-rich lichen analogs covering rocky surfaces.", adaptation: "Dense skeletal structure and wide, flat feet for weight distribution", size: "40-80 cm tall, very broad", energy_source: "Chemolithoautotrophy via mineral consumption" }, { species_name: "Nebulacetacea maxima", common_name: "Cloud Whale", description: "An enormous lighter-than-air organism that drifts through the dense upper atmosphere, filter-feeding on photosynthetic aerial microbes.", adaptation: "Hydrogen gas bladders in the thick atmosphere", size: "10-30 meters", energy_source: "Filter-feeding on photosynthetic organisms" }, { species_name: "Aurantia luminosa", common_name: "Orange Glow Fungus", description: "A bioluminescent fungal network that spans underground cave systems, glowing in response to seismic activity.", adaptation: "Piezoelectric bio-crystals that convert vibrations to light", size: "Networks spanning several meters", energy_source: "Geothermal chemosynthesis" }], habitability_assessment: "Kepler-442 b is a strong habitability candidate. Its K-dwarf host star provides stable, long-lasting energy with fewer flares than M-dwarfs. The planet is well within the habitable zone.", mission_recommendation: "A mission should include a gravitometer, deep-penetrating radar, and atmospheric sampling system to confirm liquid water presence.", fun_fact: "Kepler-442 b's year is only 112 Earth days, meaning you'd celebrate a birthday every 3.7 months!" } },
        { pl_name: "K2-18 b", host_star: "K2-18", planet_type: "Mini-Neptune", planet_type_icon: "--", equilibrium_temp_k: 255, radius_earth: 2.61, mass_earth: 8.63, habitability_score: 45, habitability_classification: "Marginal", habitability_color: "#ffaa00", orbital_distance_au: 0.1429, distance_ly: 124, discovery_method: "Transit", discovery_year: 2015, star_spectral_type: "M2.5", short_description: "A sub-Neptune world with detected atmospheric water vapor - the first of its kind - orbiting in the habitable zone of a red dwarf.", bio_report: { environment_summary: "K2-18 b likely has no solid surface to stand on. Instead, deep hydrogen-rich atmosphere blends into a global ocean of supercritical water, extending thousands of kilometers deep.", atmosphere_analysis: "JWST has detected CO2, methane, and possibly dimethyl sulfide (a biosignature on Earth). The atmosphere is hydrogen-rich with significant water content.", surface_conditions: "No rocky surface. The planet transitions from gaseous atmosphere to a deep water-world interior. Pressure increases drastically with depth.", hypothetical_lifeforms: [{ species_name: "Abyssocytus methanogenesis", common_name: "Methane Jellybell", description: "A buoyant, translucent organism floating in the upper atmosphere-ocean boundary. It metabolizes methane and hydrogen.", adaptation: "Gas-filled bladders and pressure-resistant cellular walls", size: "1-5 cm", energy_source: "Methanogenesis" }, { species_name: "Hydroborealis luminans", common_name: "Pressure Light Worm", description: "A deep-water organism that thrives at extreme pressures, producing bioluminescence to communicate in the dark ocean depths.", adaptation: "Pressure-hardened silicon-based exoskeleton", size: "10-30 cm", energy_source: "Chemosynthesis from hydrothermal vents" }, { species_name: "Neptunococcus flotans", common_name: "Sky Microbe", description: "Microscopic organisms forming vast blooms in the upper atmospheric layers, turning patches of the sky slightly greenish.", adaptation: "UV-resistant pigmentation using its star's radiation spectrum", size: "Microscopic", energy_source: "Photosynthesis in hydrogen atmosphere" }], habitability_assessment: "K2-18 b is unlikely to support surface life as we know it due to extreme pressures and no solid surface. However, the detection of potential biosignatures makes it one of the most intriguing targets for atmospheric life.", mission_recommendation: "An atmospheric entry probe with a mass spectrometer to confirm the DMS detection and characterize the atmosphere layer by layer would be invaluable.", fun_fact: "K2-18 b may contain more water than all the oceans on Earth combined - thousands of times over!" } },
        { pl_name: "TOI-700 d", host_star: "TOI-700", planet_type: "Terrestrial", planet_type_icon: "--", equilibrium_temp_k: 269, radius_earth: 1.19, mass_earth: 1.72, habitability_score: 68, habitability_classification: "Promising", habitability_color: "#88ff00", orbital_distance_au: 0.163, distance_ly: 101.4, discovery_method: "Transit", discovery_year: 2020, star_spectral_type: "M2V", short_description: "The first Earth-size planet discovered in its star's habitable zone by NASA's TESS mission - a landmark in our search for habitable worlds.", bio_report: { environment_summary: "TOI-700 d orbits a quiet M-dwarf star. The sky would appear in deep red-orange hues. Tidally locked, it has a permanent day side and night side with a habitable twilight ring.", atmosphere_analysis: "Models suggest it could sustain an atmosphere with CO2, N2 and possibly water, given its Earth-like composition and the star's relatively low flare activity.", surface_conditions: "The substellar point may feature a warm ocean surrounded by a ring of temperate land. The nightside is frozen. Massive weather systems cycle between the two hemispheres.", hypothetical_lifeforms: [{ species_name: "Terminalis migratorus", common_name: "Border Crawler", description: "Large arthropod-like creatures that walk the terminator line, always staying in the twilight band. They follow the temperature gradient for optimal conditions.", adaptation: "Wide temperature tolerance and dual-spectrum vision (infrared and visible)", size: "20-40 cm", energy_source: "Omnivorous scavenging" }, { species_name: "Rubrophyllum perpetuum", common_name: "Everdusk Tree", description: "A tree-like organism with deep-red photosynthetic leaves optimized for the M-dwarf's infrared-heavy spectrum. Found exclusively in the twilight zone.", adaptation: "Infrared-absorbing chlorophyll analog and deep root systems", size: "3-8 meters tall", energy_source: "Infrared photosynthesis" }, { species_name: "Cryovermis noctis", common_name: "Night Ice Worm", description: "Extremophile invertebrates living in the ice sheets of the nightside, surviving near geothermal vents that crack through the ice.", adaptation: "Antifreeze blood proteins and thermal-sensing tentacles", size: "5-15 cm", energy_source: "Chemosynthesis near geothermal vents" }], habitability_assessment: "TOI-700 d is among the best candidates from TESS for follow-up habitability studies. Its quiet host star reduces the threat of atmosphere-stripping flares, and its size is ideal for a rocky composition.", mission_recommendation: "A spectroscopic telescope (like JWST) should target this system for atmospheric transit spectroscopy to detect O2, O3, or H2O absorption lines.", fun_fact: "TOI-700 d was initially misclassified, and its true nature was only discovered after a high school student flagged an error in the TESS data!" } },
        { pl_name: "Proxima Centauri b", host_star: "Proxima Centauri", planet_type: "Terrestrial", planet_type_icon: "--", equilibrium_temp_k: 234, radius_earth: 1.08, mass_earth: 1.27, habitability_score: 58, habitability_classification: "Promising", habitability_color: "#88ff00", orbital_distance_au: 0.0485, distance_ly: 4.24, discovery_method: "Radial Velocity", discovery_year: 2016, star_spectral_type: "M5.5Ve", short_description: "The closest known exoplanet to Earth - orbiting our nearest stellar neighbor at just 4.24 light-years, tantalizingly within reach of future interstellar missions.", bio_report: { environment_summary: "Standing on Proxima b, the M-dwarf star would appear as a large, dim, red disc. Extreme stellar flares could turn the sky blindingly bright. The planet is likely tidally locked.", atmosphere_analysis: "Proxima Centauri's extreme flare activity may have stripped much of the atmosphere. If any remains, it would be rich in CO2 and nitrogen, possibly with water if protected by a magnetic field.", surface_conditions: "If atmosphereless, the dayside is irradiated and barren; the nightside frozen. With atmosphere, a global ocean or habitable band at the terminator is possible.", hypothetical_lifeforms: [{ species_name: "Subterracoccus radiotolerans", common_name: "Cave Sphere", description: "A radiation-resistant microbe living deep underground, protected from the surface flare bombardment. It forms spherical colonies in rock cavities.", adaptation: "Multi-layered DNA repair mechanisms and radiation-absorbing pigments", size: "Microscopic, colonial formations up to 5 cm", energy_source: "Radiolysis of subsurface water" }, { species_name: "Magnetoductus ferrovorans", common_name: "Iron Thread", description: "A filamentous organism living in iron-rich underground aquifers. It uses the planet's potential magnetic field for navigation to nutrient sources.", adaptation: "Magnetite crystals in cellular structure for geomagnetic orientation", size: "Filaments 1-10 cm long", energy_source: "Iron oxidation chemosynthesis" }, { species_name: "Corallium subglaciale", common_name: "Under-Ice Coral", description: "If subsurface oceans exist, these branching colonial organisms could form reef-like structures around hydrothermal vents beneath the nightside ice.", adaptation: "Pressurized hydraulic skeletal system and freeze-resistant tissues", size: "Colonial structures up to 1 meter", energy_source: "Hydrothermal chemosynthesis" }], habitability_assessment: "Proxima b's habitability is heavily debated. The primary challenge is Proxima Centauri's extreme flare activity, which could strip the atmosphere and irradiate the surface. Subsurface life remains plausible.", mission_recommendation: "Given its proximity, Proxima b is THE prime target for Breakthrough Starshot's laser-propelled nanocraft, which could reach it in about 20 years.", fun_fact: "At 4.24 light-years away, Proxima b is so close that a signal sent today would arrive during your next presidential election!" } },
        { pl_name: "55 Cancri e", host_star: "55 Cancri", planet_type: "Super-Earth", planet_type_icon: "--", equilibrium_temp_k: 2573, radius_earth: 1.88, mass_earth: 8.08, habitability_score: 5, habitability_classification: "Hostile", habitability_color: "#ff0044", orbital_distance_au: 0.0154, distance_ly: 41.0, discovery_method: "Radial Velocity", discovery_year: 2004, star_spectral_type: "G8V", short_description: "A searing lava world so hot its surface may be covered in oceans of molten rock, with possible diamond rain in its silicate atmosphere.", bio_report: { environment_summary: "55 Cancri e is an inferno. Temperatures on the dayside exceed 2500K. The surface is likely an ocean of flowing magma, glowing bright orange-red. Silicate vapor clouds fill the sky.", atmosphere_analysis: "The atmosphere, if present, would consist of rock vapor - vaporized silicates, metals, and possibly sodium. No hydrogen or helium can survive these temperatures.", surface_conditions: "Pure molten lava covering the dayside. The nightside, while cooler (~1400K), is still hot enough to melt most metals. Rivers of molten minerals flow across the surface.", hypothetical_lifeforms: [{ species_name: "Ignis lithobionta", common_name: "Magma Floater", description: "A hypothetical silicon-based extremophile floating on the surface of the magma ocean. Uses temperature differentials at the magma-atmosphere boundary for energy.", adaptation: "Silicon-based biochemistry operating at 2000K+", size: "Microscopic", energy_source: "Thermal gradient energy harvesting" }, { species_name: "Crystalserpens metallica", common_name: "Metal Crystal Worm", description: "A crystalline organism that grows in the cooling cracks of the nightside, where temperatures drop just enough for certain metallic crystals to form ordered structures.", adaptation: "Metallic crystal lattice body instead of carbon-based cells", size: "1-5 cm crystalline structures", energy_source: "Piezoelectric energy from tectonic stress" }, { species_name: "Nubicola ferrea", common_name: "Iron Cloud Spore", description: "Microscopic metallic spores carried in the rock-vapor atmosphere, catalyzing mineral reactions as they cycle between the extreme day and cooler night hemispheres.", adaptation: "Iron-based outer shell resistant to extreme heat", size: "Nanoscale", energy_source: "Catalytic mineral reactions" }], habitability_assessment: "55 Cancri e is almost certainly uninhabitable by any carbon-based life. However, it is one of the best-studied super-Earths and a prime laboratory for understanding rocky planet atmospheres at extreme conditions.", mission_recommendation: "JWST thermal emission mapping is already revealing its secrets. A heat-resistant atmospheric probe (if someday possible) would revolutionize our understanding of hot rocky worlds.", fun_fact: "55 Cancri e was once theorized to be made of diamond due to a high carbon-to-oxygen ratio. It could be worth $26.9 nonillion!" } }
    ];
}

function getDemoLogs() {
    return [
        { id: 1, run_type: "daily_audit", planets_scanned: 50, planets_new: 6, planets_updated: 44, bio_reports_generated: 12, status: "completed", started_at: new Date(Date.now() - 3600000).toISOString(), completed_at: new Date(Date.now() - 3300000).toISOString(), errors: [] },
        { id: 2, run_type: "daily_audit", planets_scanned: 50, planets_new: 3, planets_updated: 47, bio_reports_generated: 8, status: "completed", started_at: new Date(Date.now() - 90000000).toISOString(), completed_at: new Date(Date.now() - 89700000).toISOString(), errors: [] },
        { id: 3, run_type: "initial_scan", planets_scanned: 50, planets_new: 50, planets_updated: 0, bio_reports_generated: 50, status: "completed", started_at: new Date(Date.now() - 180000000).toISOString(), completed_at: new Date(Date.now() - 178200000).toISOString(), errors: [] },
    ];
}

// --- Render Planet Cards --- 
function renderPlanetCards(planets) {
    const grid = document.getElementById('planetGrid');
    if (!grid) return;
    grid.innerHTML = '';

    // Cleanup old card scenes
    Object.keys(cardScenes).forEach(key => {
        cancelAnimationFrame(cardScenes[key].animId);
        cardScenes[key].renderer.dispose();
    });
    cardScenes = {};

    planets.forEach((planet, index) => {
        const canvasId = `card-canvas-${index}`;
        const scoreColor = planet.habitability_color || '#888';
        const tempK = planet.equilibrium_temp_k;
        const tempC = tempK ? (tempK - 273.15).toFixed(0) : '?';

        // Parse detailed info if it's JSON
        let detailedInfo = null;
        try {
            if (planet.short_description && planet.short_description.startsWith('{')) {
                detailedInfo = JSON.parse(planet.short_description);
            }
        } catch (e) {
            console.warn("JSON parse error for planet description", e);
        }

        const card = document.createElement('div');
        card.className = 'planet-card';
        card.style.setProperty('--card-accent', `linear-gradient(90deg, ${scoreColor}, transparent)`);
        card.setAttribute('data-classification', (planet.habitability_classification || '').toLowerCase().replace(' ', ''));
        card.setAttribute('data-type', (planet.planet_type || '').toLowerCase().replace('-', ''));
        card.onclick = () => openModal(planet);

        let insightHTML = '';
        if (detailedInfo) {
            insightHTML = `
                <div class="card-insights">
                    <div class="insight-item">
                        <span class="insight-label">Weather</span>
                        <span class="insight-value">${detailedInfo.weather}</span>
                    </div>
                    <div class="insight-item">
                        <span class="insight-label">Habitability</span>
                        <span class="insight-value">${detailedInfo.habitability_insight}</span>
                    </div>
                    <div class="insight-item">
                        <span class="insight-label">Life Probability: ${detailedInfo.life_probability}</span>
                        <div class="life-probability-bar">
                            <div class="life-probability-fill" style="width: ${detailedInfo.life_probability}"></div>
                        </div>
                        <span class="insight-value" style="font-size: 0.7rem; margin-top: 4px; font-style: italic;">${detailedInfo.life_reasoning}</span>
                    </div>
                </div>
            `;
        }

        card.innerHTML = `
            <div class="card-canvas-container" id="${canvasId}">
                <div class="card-score-badge" style="background: ${scoreColor}22; color: ${scoreColor}; border-color: ${scoreColor}44">
                    ${planet.habitability_score || 0}%
                </div>
                <div class="card-type-badge">${planet.planet_type_icon || '--'} ${planet.planet_type || 'Unknown'}</div>
            </div>
            <div class="card-body">
                <div class="card-name">${planet.pl_name}</div>
                <div class="card-star">- ${planet.host_star || 'Unknown'} - ${planet.star_spectral_type || '?'} - ${planet.distance_ly ? planet.distance_ly.toFixed(1) + ' ly' : '? ly'}</div>
                ${detailedInfo ? insightHTML : `
                    <div class="card-description">
                        <div class="processing-glow"></div>
                        <span>${planet.short_description || 'AETHER Neural Link active. Characterizing planetary signatures...'}</span>
                    </div>
                `}
                <div class="card-metrics">
                    <div class="metric">
                        <div class="metric-value">${planet.radius_earth ? parseFloat(planet.radius_earth).toFixed(2) : '?'}</div>
                        <div class="metric-label">R-</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${tempC}-C</div>
                        <div class="metric-label">Temp</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" style="color: ${scoreColor}">${planet.habitability_classification || '?'}</div>
                        <div class="metric-label">Status</div>
                    </div>
                </div>
            </div>
        `;

        grid.appendChild(card);

        // Staggered 3D render for smooth loading
        setTimeout(() => renderCardPlanet(canvasId, planet), index * 100);
    });
}

// --- Filter Planets --- 
function filterPlanets(filter) {
    currentFilter = filter;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`.filter-btn[data-filter="${filter}"]`)?.classList.add('active');

    let filtered = allPlanets;
    if (filter === 'prime') {
        filtered = allPlanets.filter(p => p.habitability_score >= 70);
    } else if (filter === 'promising') {
        filtered = allPlanets.filter(p => p.habitability_score >= 50 && p.habitability_score < 70);
    } else if (filter === 'terrestrial') {
        filtered = allPlanets.filter(p => p.planet_type === 'Terrestrial');
    } else if (filter === 'supearth') {
        filtered = allPlanets.filter(p => p.planet_type === 'Super-Earth');
    }

    renderPlanetCards(filtered);
}

// --- Planet Detail Modal --- 
function openModal(planet) {
    const modal = document.getElementById('planetModal');
    const heroContainer = document.getElementById('modalHero');
    const nameEl = document.getElementById('modalPlanetName');
    const classEl = document.getElementById('modalPlanetClassification');
    const bodyEl = document.getElementById('modalBody');

    nameEl.textContent = planet.pl_name;
    classEl.textContent = `${planet.planet_type_icon || '--'} ${planet.planet_type || 'Unknown'} - ${planet.habitability_classification || 'Unclassified'} - ${planet.discovery_year || '?'}`;

    // Render hero planet (remove old canvas)
    const oldCanvas = heroContainer.querySelector('canvas');
    if (oldCanvas) oldCanvas.remove();

    const width = heroContainer.clientWidth || 900;
    const height = 300;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.z = 3.5;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x0a0f1e, 1);
    heroContainer.insertBefore(renderer.domElement, heroContainer.querySelector('.modal-hero-overlay'));

    scene.add(new THREE.AmbientLight(0x334466, 0.4));
    const light = new THREE.DirectionalLight(0xffffff, 1.3);
    light.position.set(4, 2, 5);
    scene.add(light);

    const heroMesh = createPlanetMesh(planet, 1.3);
    scene.add(heroMesh);
    function animHero() {
        requestAnimationFrame(animHero);
        heroMesh.rotation.y += 0.003;
        renderer.render(scene, camera);
    }
    animHero();

    // Build body content
    const bio = planet.bio_report || {};
    const hab = planet.habitability_breakdown || {};
    const scoreColor = planet.habitability_color || '#888';
    const tempK = planet.equilibrium_temp_k;
    const tempC = tempK ? (tempK - 273.15).toFixed(1) : '?';

    let breakdownHTML = '';
    if (hab && typeof hab === 'object') {
        Object.entries(hab).forEach(([key, val]) => {
            if (val && val.score !== undefined) {
                const pct = (val.score / val.max * 100).toFixed(0);
                breakdownHTML += `
                    <div class="breakdown-item">
                        <span>${key.charAt(0).toUpperCase() + key.slice(1)}</span>
                        <span>${val.score}/${val.max}</span>
                    </div>
                    <div class="breakdown-bar"><div class="breakdown-fill" style="width: ${pct}%"></div></div>`;
            }
        });
    }

    let lifeformsHTML = '';
    if (bio.hypothetical_lifeforms && Array.isArray(bio.hypothetical_lifeforms)) {
        lifeformsHTML = bio.hypothetical_lifeforms.map(lf => `
            <div class="lifeform-card">
                <div class="lifeform-name">${lf.species_name || 'Unknown Species'}</div>
                <div class="lifeform-common">"${lf.common_name || ''}"</div>
                <div class="lifeform-desc">${lf.description || ''}</div>
                <div>
                    <span class="lifeform-tag">-- ${lf.adaptation || '?'}</span>
                    <span class="lifeform-tag">-- ${lf.size || '?'}</span>
                    <span class="lifeform-tag">- ${lf.energy_source || '?'}</span>
                </div>
            </div>
        `).join('');
    }

    bodyEl.innerHTML = `
        <!-- Score -->
        <div class="modal-score-bar">
            <div class="score-circle" style="color: ${scoreColor}">
                ${planet.habitability_score || 0}%
            </div>
            <div class="score-details">
                <div class="score-classification" style="color: ${scoreColor}">
                    ${planet.habitability_classification || 'Unclassified'}
                </div>
                <div class="score-breakdown">${breakdownHTML}</div>
            </div>
        </div>

        <!-- Planetary Data -->
        <div class="modal-section">
            <h3>-- PLANETARY DATA</h3>
            <div class="data-grid">
                <div class="data-item"><div class="data-label">Radius</div><div class="data-value">${planet.radius_earth ? parseFloat(planet.radius_earth).toFixed(2) : '?'} R-</div></div>
                <div class="data-item"><div class="data-label">Mass</div><div class="data-value">${planet.mass_earth ? parseFloat(planet.mass_earth).toFixed(2) : '?'} M-</div></div>
                <div class="data-item"><div class="data-label">Temperature</div><div class="data-value">${tempK ? tempK + ' K (' + tempC + '-C)' : 'Unknown'}</div></div>
                <div class="data-item"><div class="data-label">Orbital Distance</div><div class="data-value">${planet.orbital_distance_au ? parseFloat(planet.orbital_distance_au).toFixed(4) + ' AU' : '?'}</div></div>
                <div class="data-item"><div class="data-label">Distance</div><div class="data-value">${planet.distance_ly ? parseFloat(planet.distance_ly).toFixed(1) + ' ly' : '?'}</div></div>
                <div class="data-item"><div class="data-label">Discovery</div><div class="data-value">${planet.discovery_method || '?'} (${planet.discovery_year || '?'})</div></div>
                <div class="data-item"><div class="data-label">Host Star</div><div class="data-value">${planet.host_star || '?'} (${planet.star_spectral_type || '?'})</div></div>
                <div class="data-item"><div class="data-label">HZ Range</div><div class="data-value">${planet.habitable_zone_inner && planet.habitable_zone_outer ? planet.habitable_zone_inner.toFixed(3) + ' - ' + planet.habitable_zone_outer.toFixed(3) + ' AU' : 'Unknown'}</div></div>
            </div>
        </div>

        <!-- AI Insights -->
        ${planet.short_description && planet.short_description.startsWith('{') ? (() => {
            try {
                const info = JSON.parse(planet.short_description);
                return `
                <div class="modal-section" style="border-top: 1px solid var(--border-subtle); padding-top: 2rem;">
                    <h3>--- ASTRO-INTELLIGENCE REPORT</h3>
                    <div class="insight-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 2rem; margin-top: 1rem;">
                        <div class="insight-card">
                            <span class="insight-label">Weather Systems</span>
                            <p style="color: var(--text-secondary); line-height: 1.6;">${info.weather}</p>
                        </div>
                        <div class="insight-card">
                            <span class="insight-label">Habitability Insight</span>
                            <p style="color: var(--text-secondary); line-height: 1.6;">${info.habitability_insight}</p>
                        </div>
                        <div class="insight-card">
                            <span class="insight-label">Current Life Probability</span>
                            <div class="life-probability-bar" style="height: 6px; margin: 10px 0;">
                                <div class="life-probability-fill" style="width: ${info.life_probability}"></div>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-family: var(--font-mono); color: var(--accent-cyan);">
                                <span>${info.life_probability}</span>
                            </div>
                            <p style="font-size: 0.8rem; font-style: italic; color: var(--text-muted); margin-top: 8px;">${info.life_reasoning}</p>
                        </div>
                    </div>
                </div>`;
            } catch(e) { return ''; }
        })() : ''}

        ${bio.environment_summary ? `
        <div class="modal-section">
            <h3>-- ENVIRONMENT</h3>
            <p>${bio.environment_summary}</p>
        </div>` : ''}

        ${bio.atmosphere_analysis ? `
        <div class="modal-section">
            <h3>--- ATMOSPHERE</h3>
            <p>${bio.atmosphere_analysis}</p>
        </div>` : ''}

        ${bio.surface_conditions ? `
        <div class="modal-section">
            <h3>--- SURFACE CONDITIONS</h3>
            <p>${bio.surface_conditions}</p>
        </div>` : ''}

        ${lifeformsHTML ? `
        <div class="modal-section">
            <h3>-- SPECULATIVE EVOLUTION - HYPOTHETICAL LIFEFORMS</h3>
            <div class="lifeform-grid">${lifeformsHTML}</div>
        </div>` : ''}

        ${bio.habitability_assessment ? `
        <div class="modal-section">
            <h3>-- HABITABILITY ASSESSMENT</h3>
            <p>${bio.habitability_assessment}</p>
        </div>` : ''}

        ${bio.mission_recommendation ? `
        <div class="modal-section">
            <h3>-- MISSION RECOMMENDATION</h3>
            <p>${bio.mission_recommendation}</p>
        </div>` : ''}

        ${bio.fun_fact ? `
        <div class="modal-section">
            <h3>-- FUN FACT</h3>
            <p>${bio.fun_fact}</p>
        </div>` : ''}
    `;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('planetModal').classList.remove('active');
    document.body.style.overflow = '';
}

// Close modal on overlay click
document.getElementById('planetModal')?.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) closeModal();
});

// Close on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

// --- Section Navigation --- 
function switchSection(section) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

    document.getElementById(`section-${section}`)?.classList.add('active');
    document.querySelector(`.nav-link[data-section="${section}"]`)?.classList.add('active');

    if (section === 'viewer' && !viewerScene) {
        initViewer();
        if (allPlanets.length > 0) loadPlanetInViewer(allPlanets[0]);
    }
}

// --- Update Stats --- 
function updateStats(planets, logs) {
    document.getElementById('statPlanets').textContent = planets.length;
    const habitable = planets.filter(p => p.habitability_score >= 55).length;
    document.getElementById('statHabitable').textContent = habitable;

    const bioCount = planets.filter(p => p.bio_report && Object.keys(p.bio_report).length > 0).length;
    document.getElementById('statBioReports').textContent = bioCount;

    document.getElementById('statMissions').textContent = logs.length;

    if (planets.length > 0) {
        const avg = Math.round(planets.reduce((sum, p) => sum + (p.habitability_score || 0), 0) / planets.length);
        document.getElementById('statAvgScore').textContent = avg + '%';
    }
}

// --- Render Mission Logs --- 
function renderMissionLogs(logs) {
    const container = document.getElementById('missionLogs');
    if (!container) return;

    if (logs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">--</div>
                <h3>NO MISSIONS YET</h3>
                <p>Run the backend mission_control.py script to start your first exoplanet scan.</p>
            </div>`;
        return;
    }

    container.innerHTML = logs.map(log => {
        const startDate = new Date(log.started_at);
        const duration = log.completed_at ? 
            Math.round((new Date(log.completed_at) - startDate) / 1000) : '-';

        return `
            <div class="log-entry">
                <div class="log-time">${startDate.toLocaleDateString()} ${startDate.toLocaleTimeString()}</div>
                <div class="log-content">
                    <div class="log-title">
                        ${log.run_type === 'daily_audit' ? '-- Daily Audit' : '-- ' + log.run_type}
                        <span class="log-status ${log.status}">${log.status}</span>
                    </div>
                    <div class="log-details">
                        Scanned ${log.planets_scanned || 0} planets - 
                        ${log.planets_new || 0} new discoveries - 
                        ${log.bio_reports_generated || 0} bio-reports - 
                        ${typeof duration === 'number' ? duration + 's' : duration}
                    </div>
                </div>
            </div>`;
    }).join('');
}

// --- Render Viewer Sidebar --- 
function renderViewerSidebar(planets) {
    const list = document.getElementById('viewerPlanetList');
    if (!list) return;

    list.innerHTML = planets.slice(0, 20).map((planet, i) => `
        <div class="viewer-planet-item ${i === 0 ? 'active' : ''}" data-name="${planet.pl_name}" onclick="loadPlanetInViewer(allPlanets[${i}])">
            <div class="viewer-planet-icon">${planet.planet_type_icon || '--'}</div>
            <div class="viewer-planet-info">
                <h4>${planet.pl_name}</h4>
                <p>${planet.habitability_score || 0}% - ${planet.planet_type || 'Unknown'}</p>
            </div>
        </div>
    `).join('');
}

// --- Render Research Papers ---
function renderResearchPapers(papers) {
    const grid = document.getElementById('researchGrid');
    if (!grid) return;

    if (papers.length === 0) {
        grid.innerHTML = '<div class="paper-summary">No research papers available in the database.</div>';
        return;
    }

    grid.innerHTML = papers.map(paper => `
        <div class="research-card">
            <div class="paper-title">${paper.title}</div>
            <div class="paper-meta">${paper.authors} | ${paper.journal} (${paper.publication_year})</div>
            <div class="paper-summary">${paper.summary}</div>
            <div class="paper-tags">
                ${(paper.tags || []).map(tag => `<span class="paper-tag">${tag}</span>`).join('')}
            </div>
            <a href="${paper.url}" target="_blank" class="paper-link">View Full Paper &rarr;</a>
        </div>
    `).join('');
}

// --- Loading Screen --- 
function hideLoading() {
    const loading = document.getElementById('loadingScreen');
    if (loading) {
        loading.classList.add('hidden');
    }
}

function updateLoadingText(text) {
    const el = document.getElementById('loadingText');
    if (el) el.textContent = text;
}

// --- Initialize Application --- 
async function init() {
    generateStars();

    updateLoadingText('CONNECTING TO DATABASE...');
    await new Promise(r => setTimeout(r, 400));

    updateLoadingText('FETCHING PLANETARY DATA...');
    allPlanets = await fetchPlanets();

    updateLoadingText('FETCHING RESEARCH REPOSITORY...');
    const papers = await fetchResearchPapers();

    updateLoadingText('LOADING MISSION LOGS...');
    const logs = await fetchMissionLogs();

    updateLoadingText('RENDERING DISCOVERY GALLERY...');
    await new Promise(r => setTimeout(r, 300));

    renderPlanetCards(allPlanets);
    updateStats(allPlanets, logs);
    renderMissionLogs(logs);
    renderViewerSidebar(allPlanets);
    renderResearchPapers(papers);

    updateLoadingText('SYSTEMS ONLINE');
    await new Promise(r => setTimeout(r, 500));
    hideLoading();

    // Update nav status
    document.getElementById('navStatusText').textContent = `${allPlanets.length} PLANETS - ONLINE`;
}

// Handle window resize for viewer
window.addEventListener('resize', () => {
    if (viewerRenderer && viewerCamera) {
        const container = document.getElementById('viewerCanvasContainer');
        if (container) {
            const w = container.clientWidth;
            const h = container.clientHeight;
            viewerCamera.aspect = w / h;
            viewerCamera.updateProjectionMatrix();
            viewerRenderer.setSize(w, h);
        }
    }
});

// --- Boot! --- 
// Safety net: force-dismiss loading screen after 8 seconds no matter what
setTimeout(() => hideLoading(), 8000);

async function boot() {
    console.log("AETHER INIT STARTING...");
    try {
        const { createClient } = await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm');
        supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        await init();
    } catch (e) {
        console.error('Init error:', e);
        // Force load demo data even if something crashes
        allPlanets = getDemoData();
        renderPlanetCards(allPlanets);
        updateStats(allPlanets, getDemoLogs());
        renderMissionLogs(getDemoLogs());
        renderViewerSidebar(allPlanets);
        hideLoading();
    }
}

// Call boot immediately (script is at end of body or deferred, DOM is ready)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
} else {
    boot();
}
