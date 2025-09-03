// 3D Floating Cubes Background
class FloatingCubes {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.cubes = [];
        this.mouse = { x: 0, y: 0 };
        
        this.init();
        this.bindEvents();
        this.animate();
    }
    
    init() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Create cubes
        for (let i = 0; i < 15; i++) {
            this.cubes.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                z: Math.random() * 1000,
                size: Math.random() * 60 + 20,
                rotationX: Math.random() * Math.PI * 2,
                rotationY: Math.random() * Math.PI * 2,
                rotationZ: Math.random() * Math.PI * 2,
                speedX: (Math.random() - 0.5) * 0.5,
                speedY: (Math.random() - 0.5) * 0.5,
                speedZ: (Math.random() - 0.5) * 0.5,
                rotSpeedX: (Math.random() - 0.5) * 0.02,
                rotSpeedY: (Math.random() - 0.5) * 0.02,
                rotSpeedZ: (Math.random() - 0.5) * 0.02,
                color: `hsl(${Math.random() * 60 + 200}, 70%, 60%)`
            });
        }
        
        window.addEventListener('resize', () => {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerHeight;
        });
    }
    
    bindEvents() {
        this.canvas.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });
    }
    
    drawCube(cube) {
        const { x, y, z, size, rotationX, rotationY, rotationZ, color } = cube;
        
        // 3D projection
        const perspective = 800;
        const scale = perspective / (perspective + z);
        const projectedX = x * scale;
        const projectedY = y * scale;
        const projectedSize = size * scale;
        
        this.ctx.save();
        this.ctx.translate(projectedX, projectedY);
        this.ctx.scale(scale, scale);
        
        // Create 3D cube effect with multiple faces
        const faces = [
            { color: this.adjustBrightness(color, 0), offset: { x: 0, y: 0 } },
            { color: this.adjustBrightness(color, -20), offset: { x: 5, y: 5 } },
            { color: this.adjustBrightness(color, -40), offset: { x: 10, y: 10 } }
        ];
        
        faces.forEach((face, index) => {
            this.ctx.fillStyle = face.color;
            this.ctx.fillRect(
                face.offset.x - projectedSize/2, 
                face.offset.y - projectedSize/2, 
                projectedSize, 
                projectedSize
            );
        });
        
        this.ctx.restore();
    }
    
    adjustBrightness(color, amount) {
        const hsl = color.match(/\d+/g);
        const lightness = Math.max(0, Math.min(100, parseInt(hsl[2]) + amount));
        return `hsl(${hsl[0]}, ${hsl[1]}%, ${lightness}%)`;
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Mouse interaction
        const mouseInfluence = 0.0001;
        
        this.cubes.forEach(cube => {
            // Mouse attraction
            const dx = this.mouse.x - cube.x;
            const dy = this.mouse.y - cube.y;
            cube.x += dx * mouseInfluence;
            cube.y += dy * mouseInfluence;
            
            // Update position
            cube.x += cube.speedX;
            cube.y += cube.speedY;
            cube.z += cube.speedZ;
            
            // Update rotation
            cube.rotationX += cube.rotSpeedX;
            cube.rotationY += cube.rotSpeedY;
            cube.rotationZ += cube.rotSpeedZ;
            
            // Boundary check
            if (cube.x < -100) cube.x = this.canvas.width + 100;
            if (cube.x > this.canvas.width + 100) cube.x = -100;
            if (cube.y < -100) cube.y = this.canvas.height + 100;
            if (cube.y > this.canvas.height + 100) cube.y = -100;
            if (cube.z < -500) cube.z = 1000;
            if (cube.z > 1000) cube.z = -500;
            
            this.drawCube(cube);
        });
        
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('cubes-canvas');
    if (canvas) {
        new FloatingCubes(canvas);
    }
});