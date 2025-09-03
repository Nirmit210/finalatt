// 3D Sphere Network Background
class SphereNetwork {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.spheres = [];
        this.connections = [];
        this.time = 0;
        this.mouse = { x: 0, y: 0 };
        
        this.init();
        this.bindEvents();
        this.animate();
    }
    
    init() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Create spheres in 3D space
        for (let i = 0; i < 25; i++) {
            this.spheres.push({
                x: (Math.random() - 0.5) * 800,
                y: (Math.random() - 0.5) * 600,
                z: (Math.random() - 0.5) * 400,
                originalX: (Math.random() - 0.5) * 800,
                originalY: (Math.random() - 0.5) * 600,
                originalZ: (Math.random() - 0.5) * 400,
                radius: Math.random() * 20 + 10,
                speedX: (Math.random() - 0.5) * 2,
                speedY: (Math.random() - 0.5) * 2,
                speedZ: (Math.random() - 0.5) * 2,
                color: `hsl(${Math.random() * 360}, 70%, 60%)`,
                pulsePhase: Math.random() * Math.PI * 2,
                connections: []
            });
        }
        
        window.addEventListener('resize', () => {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerHeight;
        });
    }
    
    bindEvents() {
        this.canvas.addEventListener('mousemove', (e) => {
            this.mouse.x = (e.clientX - this.canvas.width / 2);
            this.mouse.y = (e.clientY - this.canvas.height / 2);
        });
    }
    
    project3D(x, y, z) {
        const perspective = 800;
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        const scale = perspective / (perspective + z);
        return {
            x: centerX + x * scale,
            y: centerY + y * scale,
            scale: scale
        };
    }
    
    findConnections() {
        this.connections = [];
        
        for (let i = 0; i < this.spheres.length; i++) {
            this.spheres[i].connections = [];
            
            for (let j = i + 1; j < this.spheres.length; j++) {
                const dx = this.spheres[i].x - this.spheres[j].x;
                const dy = this.spheres[i].y - this.spheres[j].y;
                const dz = this.spheres[i].z - this.spheres[j].z;
                const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
                
                if (distance < 150) {
                    this.connections.push({
                        sphere1: i,
                        sphere2: j,
                        distance: distance,
                        strength: 1 - (distance / 150)
                    });
                    
                    this.spheres[i].connections.push(j);
                    this.spheres[j].connections.push(i);
                }
            }
        }
    }
    
    drawSphere(sphere, index) {
        const projected = this.project3D(sphere.x, sphere.y, sphere.z);
        
        // Pulsing effect
        const pulseSize = sphere.radius + Math.sin(this.time * 2 + sphere.pulsePhase) * 3;
        const finalRadius = pulseSize * projected.scale;
        
        // Mouse interaction
        const mouseDistance = Math.sqrt(
            Math.pow(this.mouse.x - (projected.x - this.canvas.width / 2), 2) +
            Math.pow(this.mouse.y - (projected.y - this.canvas.height / 2), 2)
        );
        
        const mouseEffect = Math.max(0, 1 - mouseDistance / 100);
        const glowRadius = finalRadius + mouseEffect * 20;
        
        // Draw glow
        const gradient = this.ctx.createRadialGradient(
            projected.x, projected.y, 0,
            projected.x, projected.y, glowRadius
        );
        
        const alpha = projected.scale * 0.8 + mouseEffect * 0.5;
        gradient.addColorStop(0, sphere.color.replace('60%)', `${60 + mouseEffect * 20}%)`));
        gradient.addColorStop(0.7, sphere.color.replace('60%)', '30%)').replace('hsl', 'hsla').replace(')', ', 0.3)'));
        gradient.addColorStop(1, 'transparent');
        
        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.arc(projected.x, projected.y, glowRadius, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Draw core sphere
        this.ctx.fillStyle = sphere.color;
        this.ctx.beginPath();
        this.ctx.arc(projected.x, projected.y, finalRadius, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Draw highlight
        const highlightGradient = this.ctx.createRadialGradient(
            projected.x - finalRadius * 0.3, projected.y - finalRadius * 0.3, 0,
            projected.x, projected.y, finalRadius
        );
        highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
        highlightGradient.addColorStop(1, 'transparent');
        
        this.ctx.fillStyle = highlightGradient;
        this.ctx.beginPath();
        this.ctx.arc(projected.x, projected.y, finalRadius, 0, Math.PI * 2);
        this.ctx.fill();
    }
    
    drawConnections() {
        this.connections.forEach(connection => {
            const sphere1 = this.spheres[connection.sphere1];
            const sphere2 = this.spheres[connection.sphere2];
            
            const proj1 = this.project3D(sphere1.x, sphere1.y, sphere1.z);
            const proj2 = this.project3D(sphere2.x, sphere2.y, sphere2.z);
            
            const alpha = connection.strength * 0.5 * Math.min(proj1.scale, proj2.scale);
            
            // Create gradient line
            const gradient = this.ctx.createLinearGradient(
                proj1.x, proj1.y, proj2.x, proj2.y
            );
            gradient.addColorStop(0, `rgba(100, 150, 255, ${alpha})`);
            gradient.addColorStop(0.5, `rgba(150, 100, 255, ${alpha * 1.5})`);
            gradient.addColorStop(1, `rgba(255, 100, 150, ${alpha})`);
            
            this.ctx.strokeStyle = gradient;
            this.ctx.lineWidth = connection.strength * 3;
            this.ctx.beginPath();
            this.ctx.moveTo(proj1.x, proj1.y);
            this.ctx.lineTo(proj2.x, proj2.y);
            this.ctx.stroke();
        });
    }
    
    animate() {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.time += 0.02;
        
        // Update sphere positions
        this.spheres.forEach((sphere, index) => {
            // Orbital motion
            sphere.x = sphere.originalX + Math.sin(this.time + index) * 50;
            sphere.y = sphere.originalY + Math.cos(this.time * 0.8 + index) * 30;
            sphere.z = sphere.originalZ + Math.sin(this.time * 0.6 + index) * 40;
            
            // Mouse attraction
            const mouseInfluence = 0.001;
            const dx = this.mouse.x - sphere.x;
            const dy = this.mouse.y - sphere.y;
            sphere.x += dx * mouseInfluence;
            sphere.y += dy * mouseInfluence;
        });
        
        // Update connections
        this.findConnections();
        
        // Draw connections first (behind spheres)
        this.drawConnections();
        
        // Draw spheres
        this.spheres
            .sort((a, b) => b.z - a.z) // Sort by depth
            .forEach((sphere, index) => {
                this.drawSphere(sphere, index);
            });
        
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('spheres-canvas');
    if (canvas) {
        new SphereNetwork(canvas);
    }
});