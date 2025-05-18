// 🎯 Initializes renderer only (no objects or scene logic)
const renderer = new THREE.WebGLRenderer({
  canvas: document.getElementById('bgCanvas'),
  antialias: true,
  alpha: true
});
renderer.setSize(window.innerWidth, window.innerHeight);

// 📐 Auto-resize canvas if screen changes
window.addEventListener('resize', () => {
  const aspect = window.innerWidth / window.innerHeight;
  renderer.setSize(window.innerWidth, window.innerHeight);
});
