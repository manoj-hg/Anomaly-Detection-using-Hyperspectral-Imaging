// Advanced Animations & 3D Visualization
// Three.js, GSAP, tsParticles, D3.js Integration

// Performance optimization: Lazy load Three.js only when needed
let threeInitialized = false;
let scene, camera, renderer, globe, particles, terrain;
let isAnimating = true;

function initThreeJS() {
    if (threeInitialized) return;
    
    const container = document.getElementById('three-container');
    if (!container) return;

    // Check if container is visible
    const rect = container.getBoundingClientRect();
    if (rect.top > window.innerHeight || rect.bottom < 0) {
        // Container not in viewport, defer initialization
        setTimeout(initThreeJS, 500);
        return;
    }

    threeInitialized = true;

    // Scene
    scene = new THREE.Scene();
    
    // Camera
    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.z = 5;

    // Renderer with performance optimizations
    renderer = new THREE.WebGLRenderer({ 
        antialias: false, // Disabled for better performance
        alpha: true,
        powerPreference: "high-performance",
        stencil: false,
        depth: false
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5)); // Further reduced for performance
    container.appendChild(renderer.domElement);

    // Create Globe with lower detail
    const geometry = new THREE.IcosahedronGeometry(2, 1); // Reduced detail from 2 to 1
    const material = new THREE.MeshBasicMaterial({
        color: 0x00F2FF,
        wireframe: true,
        transparent: true,
        opacity: 0.3
    });
    globe = new THREE.Mesh(geometry, material);
    scene.add(globe);

    // Create Particles around globe - reduced count
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 500; // Reduced from 1000
    const posArray = new Float32Array(particlesCount * 3);

    for (let i = 0; i < particlesCount * 3; i++) {
        posArray[i] = (Math.random() - 0.5) * 10;
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const particlesMaterial = new THREE.PointsMaterial({
        size: 0.02,
        color: 0xBC13FE,
        transparent: true,
        opacity: 0.8
    });
    particles = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particles);

    // Create Terrain visualization (data viz)
    const terrainGeometry = new THREE.PlaneGeometry(4, 4, 32, 32);
    const terrainVertices = terrainGeometry.attributes.position.array;
    
    // Add height variation for terrain effect
    for (let i = 0; i < terrainVertices.length; i += 3) {
        const x = terrainVertices[i];
        const y = terrainVertices[i + 1];
        terrainVertices[i + 2] = Math.sin(x * 2) * Math.cos(y * 2) * 0.3;
    }
    
    terrainGeometry.computeVertexNormals();
    
    const terrainMaterial = new THREE.MeshBasicMaterial({
        color: 0x39FF14,
        wireframe: true,
        transparent: true,
        opacity: 0.2
    });
    terrain = new THREE.Mesh(terrainGeometry, terrainMaterial);
    terrain.rotation.x = -Math.PI / 2;
    terrain.position.y = -2;
    scene.add(terrain);

    // Ambient Light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    // Point Light
    const pointLight = new THREE.PointLight(0x00F2FF, 1);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    // Handle Resize with debounce
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }, 250);
    });

    // Pause animation when not visible
    document.addEventListener('visibilitychange', () => {
        isAnimating = !document.hidden;
        if (isAnimating) animate();
    });

    animate();
}

let animationFrameId;
function animate() {
    if (!isAnimating) return;
    
    animationFrameId = requestAnimationFrame(animate);

    if (globe) {
        globe.rotation.x += 0.001;
        globe.rotation.y += 0.002;
    }

    if (particles) {
        particles.rotation.y -= 0.0005;
    }

    if (terrain) {
        terrain.rotation.z += 0.001;
    }

    renderer.render(scene, camera);
}

// tsParticles Configuration with performance optimization
let particlesInitialized = false;
function initParticles() {
    if (particlesInitialized) return;
    
    const container = document.getElementById('tsparticles');
    if (!container) return;

    particlesInitialized = true;

    tsParticles.load("tsparticles", {
        particles: {
            number: {
                value: 60, // Reduced from 80 for better performance
                density: {
                    enable: true,
                    value_area: 800
                }
            },
            color: {
                value: ["#00F2FF", "#BC13FE", "#39FF14"]
            },
            shape: {
                type: "circle"
            },
            opacity: {
                value: 0.4, // Slightly reduced for performance
                random: true,
                anim: {
                    enable: true,
                    speed: 1,
                    opacity_min: 0.1,
                    sync: false
                }
            },
            size: {
                value: 2.5, // Slightly reduced
                random: true,
                anim: {
                    enable: true,
                    speed: 2,
                    size_min: 0.1,
                    sync: false
                }
            },
            line_linked: {
                enable: true,
                distance: 150,
                color: "#00F2FF",
                opacity: 0.15, // Reduced for performance
                width: 1
            },
            move: {
                enable: true,
                speed: 0.8, // Slightly slower for performance
                direction: "none",
                random: true,
                straight: false,
                out_mode: "out",
                bounce: false
            }
        },
        interactivity: {
            detect_on: "canvas",
            events: {
                onhover: {
                    enable: true,
                    mode: "grab"
                },
                onclick: {
                    enable: true,
                    mode: "push"
                },
                resize: true
            },
            modes: {
                grab: {
                    distance: 140,
                    line_linked: {
                        opacity: 0.5
                    }
                },
                push: {
                    particles_nb: 4
                }
            }
        },
        retina_detect: false // Disabled for performance
    });
}

// GSAP Animations with Timeline and Parallax
function initGSAP() {
    gsap.registerPlugin(ScrollTrigger);

    // Hero Section Timeline Animation
    const heroTimeline = gsap.timeline({ defaults: { ease: "power3.out" } });
    
    heroTimeline
        .from(".hero-title .title-line", {
            y: 50,
            opacity: 0,
            duration: 1,
            stagger: 0.2
        })
        .from(".hero-subtitle", {
            y: 30,
            opacity: 0,
            duration: 1
        }, "-=0.5")
        .from(".hero-stat", {
            y: 30,
            opacity: 0,
            duration: 0.8,
            stagger: 0.1
        }, "-=0.5")
        .from(".hero-actions .btn", {
            y: 30,
            opacity: 0,
            duration: 0.8,
            stagger: 0.2
        }, "-=0.5");

    // Feature Cards Animation - one-time only
    gsap.from(".feature-card", {
        scrollTrigger: {
            trigger: ".features-section",
            start: "top 80%",
            toggleActions: "play none none none"
        },
        y: 50,
        opacity: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: "power2.out"
    });

    // Frame Animation - only for landing page visualization section, not domain pages
    gsap.from(".visualization-section .frame", {
        scrollTrigger: {
            trigger: ".visualization-section",
            start: "top 85%",
            toggleActions: "play none none none"
        },
        y: 30,
        opacity: 0,
        duration: 0.6,
        stagger: 0.1,
        ease: "power2.out"
    });

    // Navigation Animation
    gsap.from(".nav-btn", {
        x: -30,
        opacity: 0,
        duration: 0.6,
        stagger: 0.1,
        ease: "power2.out"
    });

    // Parallax for Hero Section
    gsap.to(".hero-visual", {
        scrollTrigger: {
            trigger: ".hero-section",
            start: "top top",
            end: "bottom top",
            scrub: true
        },
        y: 100,
        ease: "none"
    });

    // Parallax for Feature Cards
    gsap.utils.toArray(".feature-card").forEach((card, i) => {
        gsap.to(card, {
            scrollTrigger: {
                trigger: card,
                start: "top bottom",
                end: "bottom top",
                scrub: true
            },
            y: -30,
            ease: "none"
        });
    });
}

// Page Transition Animation
function animatePageTransition(pageId) {
    const page = document.getElementById(pageId);
    if (!page) return;

    gsap.fromTo(page, 
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }
    );
}

// Enhanced Button Hover Effects with Ripple
function initButtonEffects() {
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            gsap.to(btn, {
                scale: 1.05,
                boxShadow: "0 8px 25px rgba(0, 242, 255, 0.3)",
                duration: 0.3,
                ease: "power2.out"
            });
        });

        btn.addEventListener('mouseleave', () => {
            gsap.to(btn, {
                scale: 1,
                boxShadow: "0 4px 15px rgba(0, 242, 255, 0.2)",
                duration: 0.3,
                ease: "power2.out"
            });
        });

        btn.addEventListener('click', (e) => {
            // Ripple effect
            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            const rect = btn.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = e.clientX - rect.left - size / 2 + 'px';
            ripple.style.top = e.clientY - rect.top - size / 2 + 'px';
            
            btn.style.position = 'relative';
            btn.style.overflow = 'hidden';
            btn.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
            
            gsap.to(btn, {
                scale: 0.95,
                duration: 0.1,
                yoyo: true,
                repeat: 1,
                ease: "power2.out"
            });
        });
    });
}

// Enhanced Card Hover Effects - no tilt
function initCardEffects() {
    const cards = document.querySelectorAll('.frame, .feature-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            gsap.to(card, {
                y: -5,
                boxShadow: "0 12px 40px rgba(0, 242, 255, 0.25)",
                duration: 0.3,
                ease: "power2.out"
            });
        });

        card.addEventListener('mouseleave', () => {
            gsap.to(card, {
                y: 0,
                boxShadow: "0 4px 20px rgba(0, 0, 0, 0.3)",
                duration: 0.3,
                ease: "power2.out"
            });
        });
    });
}

// D3.js Advanced Visualization with Interactive Controls
let heatmapData = [];
function initD3Visualization(detectionData = null) {
    // Create a heatmap visualization
    const container = document.getElementById('d3-heatmap');
    if (!container) return;

    const width = container.clientWidth || 400;
    const height = 300;

    // Clear existing
    d3.select(container).selectAll("*").remove();

    const svg = d3.select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    // Use real detection data if available, otherwise generate placeholder
    heatmapData = [];
    if (detectionData && detectionData.anomaly_scores) {
        // Use real anomaly scores for heatmap
        const scores = detectionData.anomaly_scores;
        const h = scores.length;
        const w = scores[0].length;
        for (let i = 0; i < h; i++) {
            for (let j = 0; j < w; j++) {
                heatmapData.push({
                    x: j,
                    y: i,
                    value: scores[i][j] || 0
                });
            }
        }
    } else {
        // Generate placeholder data (will be replaced with real data after detection)
        for (let i = 0; i < 20; i++) {
            for (let j = 0; j < 20; j++) {
                heatmapData.push({
                    x: i,
                    y: j,
                    value: 0
                });
            }
        }
    }

    const cellSize = width / Math.max(20, Math.sqrt(heatmapData.length));

    const colorScale = d3.scaleSequential()
        .domain([0, 1])
        .interpolator(d3.interpolateViridis);

    svg.selectAll("rect")
        .data(heatmapData)
        .enter()
        .append("rect")
        .attr("x", d => d.x * cellSize)
        .attr("y", d => d.y * (height / Math.max(20, Math.sqrt(heatmapData.length))))
        .attr("width", cellSize - 1)
        .attr("height", (height / Math.max(20, Math.sqrt(heatmapData.length))) - 1)
        .attr("fill", d => colorScale(d.value))
        .attr("opacity", 0)
        .transition()
        .duration(500)
        .delay((d, i) => i * 5)
        .attr("opacity", 0.8);

    // Add intensity control
    const intensitySlider = document.getElementById('heatmap-intensity');
    if (intensitySlider) {
        intensitySlider.addEventListener('input', (e) => {
            const intensity = e.target.value / 100;
            svg.selectAll("rect")
                .attr("opacity", d => d.value * intensity + 0.2);
        });
    }

    // Add animation toggle
    const animateCheckbox = document.getElementById('heatmap-animate');
    if (animateCheckbox) {
        animateCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                svg.selectAll("rect")
                    .transition()
                    .duration(500)
                    .delay((d, i) => i * 5)
                    .attr("opacity", 0.8);
            }
        });
    }
}

// Hyperspectral Data Visualization with Interactive Filtering
let spectralMaterials = [];
function initHyperspectralVisualization(spectralData = null) {
    const container = document.getElementById('hyperspectral-viz');
    if (!container) return;

    const width = container.clientWidth || 600;
    const height = 350;
    const margin = { top: 40, right: 60, bottom: 60, left: 70 };

    // Clear existing
    d3.select(container).selectAll("*").remove();

    const svg = d3.select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    // Spectral bands (Sentinel-2 bands)
    const bands = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12'];
    const wavelengths = [490, 560, 665, 705, 740, 783, 842, 865, 1610, 2190];

    // Use real spectral data if available, otherwise use reference signatures
    if (spectralData && spectralData.bands && spectralData.values) {
        // Use real spectral data from detection
        spectralMaterials = [
            {
                name: 'Detected',
                color: '#FF0000',
                values: spectralData.values
            }
        ];
    } else {
        // Use reference spectral signatures for different materials
        spectralMaterials = [
            {
                name: 'Vegetation',
                color: '#39FF14',
                values: [0.05, 0.1, 0.08, 0.4, 0.6, 0.7, 0.75, 0.72, 0.3, 0.15]
            },
            {
                name: 'Water',
                color: '#00F2FF',
                values: [0.1, 0.05, 0.02, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            },
            {
                name: 'Soil',
                color: '#BC13FE',
                values: [0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.42, 0.43, 0.5, 0.55]
            },
            {
                name: 'Urban',
                color: '#FFA500',
                values: [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.52, 0.6, 0.65]
            }
        ];
    }

    // Create scales
    const xScale = d3.scaleLinear()
        .domain([400, 2300])
        .range([margin.left, width - margin.right]);

    const yScale = d3.scaleLinear()
        .domain([0, 0.8])
        .range([height - margin.bottom, margin.top]);

    // Create line generator
    const line = d3.line()
        .x((d, i) => xScale(wavelengths[i]))
        .y(d => yScale(d))
        .curve(d3.curveMonotoneX);

    // Add X axis
    svg.append("g")
        .attr("transform", `translate(0, ${height - margin.bottom})`)
        .call(d3.axisBottom(xScale)
            .tickFormat(d => d + "nm")
            .ticks(10))
        .attr("color", "#00F2FF")
        .selectAll("text")
        .attr("fill", "#e0e0e0")
        .attr("font-family", "'JetBrains Mono', monospace");

    // Add Y axis
    svg.append("g")
        .attr("transform", `translate(${margin.left}, 0)`)
        .call(d3.axisLeft(yScale))
        .attr("color", "#00F2FF")
        .selectAll("text")
        .attr("fill", "#e0e0e0")
        .attr("font-family", "'JetBrains Mono', monospace");

    // Add axis labels
    svg.append("text")
        .attr("text-anchor", "middle")
        .attr("x", width / 2)
        .attr("y", height - 10)
        .text("Wavelength (nm)")
        .attr("fill", "#e0e0e0")
        .attr("font-family", "'Orbitron', sans-serif")
        .attr("font-size", "12px");

    svg.append("text")
        .attr("text-anchor", "middle")
        .attr("transform", "rotate(-90)")
        .attr("x", -(height / 2))
        .attr("y", 20)
        .text("Reflectance")
        .attr("fill", "#e0e0e0")
        .attr("font-family", "'Orbitron', sans-serif")
        .attr("font-size", "12px");

    // Add grid lines
    svg.append("g")
        .attr("class", "grid")
        .attr("transform", `translate(0, ${height - margin.bottom})`)
        .call(d3.axisBottom(xScale)
            .tickSize(-(height - margin.top - margin.bottom))
            .tickFormat(""))
        .attr("stroke", "rgba(0, 242, 255, 0.1)")
        .attr("stroke-dasharray", "3,3");

    svg.append("g")
        .attr("class", "grid")
        .attr("transform", `translate(${margin.left}, 0)`)
        .call(d3.axisLeft(yScale)
            .tickSize(-(width - margin.left - margin.right))
            .tickFormat(""))
        .attr("stroke", "rgba(0, 242, 255, 0.1)")
        .attr("stroke-dasharray", "3,3");

    // Draw spectral signatures
    spectralMaterials.forEach((material, index) => {
        // Draw line
        const path = svg.append("path")
            .datum(material.values)
            .attr("fill", "none")
            .attr("stroke", material.color)
            .attr("stroke-width", 2.5)
            .attr("d", line)
            .attr("opacity", 0)
            .attr("class", `spectral-line-${index}`);

        // Animate line
        path.transition()
            .duration(1000)
            .delay(index * 200)
            .attr("opacity", 1);

        // Add dots
        svg.selectAll(`.dot-${index}`)
            .data(material.values)
            .enter()
            .append("circle")
            .attr("cx", (d, i) => xScale(wavelengths[i]))
            .attr("cy", d => yScale(d))
            .attr("r", 4)
            .attr("fill", material.color)
            .attr("stroke", "#0A0A12")
            .attr("stroke-width", 2)
            .attr("opacity", 0)
            .attr("class", `spectral-dot-${index}`)
            .transition()
            .duration(500)
            .delay(index * 200 + 800)
            .attr("opacity", 1);
    });

    // Add legend
    const legend = svg.append("g")
        .attr("transform", `translate(${width - margin.right - 100}, ${margin.top})`);

    spectralMaterials.forEach((material, index) => {
        const legendItem = legend.append("g")
            .attr("transform", `translate(0, ${index * 25})`);

        legendItem.append("rect")
            .attr("width", 15)
            .attr("height", 15)
            .attr("fill", material.color)
            .attr("rx", 3)
            .attr("opacity", 0)
            .transition()
            .duration(500)
            .delay(index * 200 + 1200)
            .attr("opacity", 1);

        legendItem.append("text")
            .attr("x", 20)
            .attr("y", 12)
            .text(material.name)
            .attr("fill", "#e0e0e0")
            .attr("font-family", "'JetBrains Mono', monospace")
            .attr("font-size", "11px")
            .attr("opacity", 0)
            .transition()
            .duration(500)
            .delay(index * 200 + 1200)
            .attr("opacity", 1);
    });

    // Add title
    svg.append("text")
        .attr("x", width / 2)
        .attr("y", 25)
        .attr("text-anchor", "middle")
        .text("Hyperspectral Signatures")
        .attr("fill", "#00F2FF")
        .attr("font-family", "'Orbitron', sans-serif")
        .attr("font-size", "14px")
        .attr("font-weight", "600")
        .attr("opacity", 0)
        .transition()
        .duration(500)
        .attr("opacity", 1);

    // Add filtering controls
    addSpectralFilters();
}

function addSpectralFilters() {
    const checkboxes = {
        'show-vegetation': 0,
        'show-water': 1,
        'show-soil': 2,
        'show-urban': 3
    };

    Object.keys(checkboxes).forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox) {
            checkbox.addEventListener('change', (e) => {
                const index = checkboxes[id];
                const line = d3.select(`.spectral-line-${index}`);
                const dots = d3.selectAll(`.spectral-dot-${index}`);
                
                if (e.target.checked) {
                    line.transition().duration(300).attr("opacity", 1);
                    dots.transition().duration(300).attr("opacity", 1);
                } else {
                    line.transition().duration(300).attr("opacity", 0);
                    dots.transition().duration(300).attr("opacity", 0);
                }
            });
        }
    });
}

// Enhanced Chart Animations
function enhanceCharts() {
    // Animate existing charts
    const charts = document.querySelectorAll('canvas');
    charts.forEach(canvas => {
        gsap.from(canvas, {
            opacity: 0,
            scale: 0.9,
            duration: 0.8,
            ease: "power2.out"
        });
    });
}

// Enhanced Loading Animation with Progress
function showLoadingAnimation() {
    const loading = document.getElementById('loadingOverlay');
    if (!loading) return;

    gsap.to(loading, {
        opacity: 1,
        duration: 0.3,
        ease: "power2.out"
    });

    // Animate spinner
    const spinner = loading.querySelector('.spinner');
    if (spinner) {
        gsap.fromTo(spinner, 
            { rotation: 0 },
            { rotation: 360, duration: 1, repeat: -1, ease: "none" }
        );
    }

    // Pulse effect
    gsap.to(loading, {
        scale: 1.02,
        duration: 0.5,
        yoyo: true,
        repeat: -1,
        ease: "power1.inOut"
    });
}

function hideLoadingAnimation() {
    const loading = document.getElementById('loadingOverlay');
    if (!loading) return;

    // Stop animations
    const spinner = loading.querySelector('.spinner');
    if (spinner) {
        gsap.killTweensOf(spinner);
    }
    gsap.killTweensOf(loading);

    gsap.to(loading, {
        opacity: 0,
        scale: 1,
        duration: 0.4,
        ease: "power2.out",
        onComplete: () => {
            loading.style.display = 'none';
        }
    });
}

// Initialize All Animations
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Three.js
    initThreeJS();
    
    // Initialize Particles
    initParticles();
    
    // Initialize GSAP
    initGSAP();
    
    // Initialize Button Effects
    initButtonEffects();
    
    // Initialize Card Effects
    initCardEffects();
    
    // Initialize D3 Visualization
    setTimeout(initD3Visualization, 1000);
    
    // Initialize Hyperspectral Visualization
    setTimeout(initHyperspectralVisualization, 1500);
    
    // Enhance Charts
    setTimeout(enhanceCharts, 500);
});

// Export functions for use in main app
window.animationUtils = {
    animatePageTransition,
    showLoadingAnimation,
    hideLoadingAnimation,
    initD3Visualization
};
