// 3D Geometric Shapes Background
class GeometricShapes3D {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.shapes = [];
        this.time = 0;
        this.mouse = { x: 0, y: 0 };
        
        this.init();
        this.bindEvents();
        this.animate();
    }
    
    init() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Create various 3D shapes
        const shapeTypes = ['tetrahedron', 'octahedron', 'cube', 'pyramid'];
        
        for (let i = 0; i < 12; i++) {
            this.shapes.push({
                type: shapeTypes[Math.floor(Math.random() * shapeTypes.length)],
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                z: Math.random() * 500 - 250,
                size: Math.random() * 80 + 40,
                rotationX: Math.random() * Math.PI * 2,
                rotationY: Math.random() * Math.PI * 2,
                rotationZ: Math.random() * Math.PI * 2,
                speedX: (Math.random() - 0.5) * 2,
                speedY: (Math.random() - 0.5) * 2,
                speedZ: (Math.random() - 0.5) * 2,
                rotSpeedX: (Math.random() - 0.5) * 0.05,
                rotSpeedY: (Math.random() - 0.5) * 0.05,
                rotSpeedZ: (Math.random() - 0.5) * 0.05,
                color: `hsl(${Math.random() * 360}, 70%, 60%)`
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
    
    project3D(x, y, z) {
        const perspective = 600;
        const scale = perspective / (perspective + z);
        return {
            x: x * scale,
            y: y * scale,
            scale: scale
        };
    }
    
    rotatePoint(x, y, z, rotX, rotY, rotZ) {
        // Rotate around X axis
        let newY = y * Math.cos(rotX) - z * Math.sin(rotX);
        let newZ = y * Math.sin(rotX) + z * Math.cos(rotX);
        y = newY;
        z = newZ;
        
        // Rotate around Y axis
        let newX = x * Math.cos(rotY) + z * Math.sin(rotY);
        newZ = -x * Math.sin(rotY) + z * Math.cos(rotY);
        x = newX;
        z = newZ;
        
        // Rotate around Z axis
        newX = x * Math.cos(rotZ) - y * Math.sin(rotZ);
        newY = x * Math.sin(rotZ) + y * Math.cos(rotZ);
        
        return { x: newX, y: newY, z: newZ };
    }
    
    drawTetrahedron(shape) {
        const { x, y, z, size, rotationX, rotationY, rotationZ, color } = shape;
        
        // Tetrahedron vertices
        const vertices = [
            { x: 0, y: -size/2, z: 0 },
            { x: -size/2, y: size/2, z: -size/2 },
            { x: size/2, y: size/2, z: -size/2 },
            { x: 0, y: size/2, z: size/2 }
        ];
        
        // Rotate and project vertices
        const projectedVertices = vertices.map(vertex => {
            const rotated = this.rotatePoint(vertex.x, vertex.y, vertex.z, rotationX, rotationY, rotationZ);
            return this.project3D(x + rotated.x, y + rotated.y, z + rotated.z);
        });
        
        // Draw faces
        const faces = [
            [0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 2, 3]
        ];
        
        faces.forEach((face, index) => {
            this.ctx.fillStyle = this.adjustBrightness(color, -index * 15);
            this.ctx.beginPath();
            this.ctx.moveTo(projectedVertices[face[0]].x, projectedVertices[face[0]].y);
            this.ctx.lineTo(projectedVertices[face[1]].x, projectedVertices[face[1]].y);
            this.ctx.lineTo(projectedVertices[face[2]].x, projectedVertices[face[2]].y);
            this.ctx.closePath();
            this.ctx.fill();
            this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
            this.ctx.stroke();
        });
    }
    
    drawCube(shape) {
        const { x, y, z, size, rotationX, rotationY, rotationZ, color } = shape;
        const half = size / 2;
        
        // Cube vertices
        const vertices = [
            { x: -half, y: -half, z: -half },
            { x: half, y: -half, z: -half },
            { x: half, y: half, z: -half },
            { x: -half, y: half, z: -half },
            { x: -half, y: -half, z: half },
            { x: half, y: -half, z: half },
            { x: half, y: half, z: half },
            { x: -half, y: half, z: half }
        ];
        
        // Rotate and project vertices
        const projectedVertices = vertices.map(vertex => {
            const rotated = this.rotatePoint(vertex.x, vertex.y, vertex.z, rotationX, rotationY, rotationZ);
            return this.project3D(x + rotated.x, y + rotated.y, z + rotated.z);
        });
        
        // Draw faces
        const faces = [
            [0, 1, 2, 3], // front
            [4, 5, 6, 7], // back
            [0, 1, 5, 4], // bottom
            [2, 3, 7, 6], // top
            [0, 3, 7, 4], // left
            [1, 2, 6, 5]  // right
        ];
        
        faces.forEach((face, index) => {
            this.ctx.fillStyle = this.adjustBrightness(color, -index * 10);
            this.ctx.beginPath();
            this.ctx.moveTo(projectedVertices[face[0]].x, projectedVertices[face[0]].y);
            for (let i = 1; i < face.length; i++) {
                this.ctx.lineTo(projectedVertices[face[i]].x, projectedVertices[face[i]].y);
            }
            this.ctx.closePath();
            this.ctx.fill();
            this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
            this.ctx.stroke();
        });
    }
    
    adjustBrightness(color, amount) {
        const hsl = color.match(/\d+/g);
        const lightness = Math.max(0, Math.min(100, parseInt(hsl[2]) + amount));
        return `hsl(${hsl[0]}, ${hsl[1]}%, ${lightness}%)`;
    }
    
    animate() {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.time += 0.01;
        
        // Mouse interaction
        const mouseInfluence = 0.0005;
        
        this.shapes.forEach(shape => {
            // Mouse attraction
            const dx = this.mouse.x - shape.x;
            const dy = this.mouse.y - shape.y;
            shape.x += dx * mouseInfluence;
            shape.y += dy * mouseInfluence;
            
            // Update position
            shape.x += shape.speedX;
            shape.y += shape.speedY;
            shape.z += shape.speedZ;
            
            // Update rotation
            shape.rotationX += shape.rotSpeedX;
            shape.rotationY += shape.rotSpeedY;
            shape.rotationZ += shape.rotSpeedZ;
            
            // Boundary check
            if (shape.x < -100) shape.x = this.canvas.width + 100;
            if (shape.x > this.canvas.width + 100) shape.x = -100;
            if (shape.y < -100) shape.y = this.canvas.height + 100;
            if (shape.y > this.canvas.height + 100) shape.y = -100;
            if (shape.z < -300) shape.z = 300;
            if (shape.z > 300) shape.z = -300;
            
            // Draw shape based on type
            if (shape.type === 'tetrahedron') {
                this.drawTetrahedron(shape);
            } else if (shape.type === 'cube') {
                this.drawCube(shape);
            }
        });
        
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('geometry-canvas');
    if (canvas) {
        new GeometricShapes3D(canvas);
    }
});