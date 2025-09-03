// 3D DNA Helix Background
class DNAHelix {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.helixes = [];
        this.time = 0;
        this.mouse = { x: 0, y: 0 };
        
        this.init();
        this.bindEvents();
        this.animate();
    }
    
    init() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Create multiple DNA helixes
        for (let h = 0; h < 3; h++) {
            const helix = {
                x: (this.canvas.width / 4) * (h + 1),
                y: this.canvas.height / 2,
                points: [],
                connections: [],
                radius: 80 + h * 20,
                height: 600,
                segments: 100,
                color1: `hsl(${120 + h * 60}, 70%, 60%)`,
                color2: `hsl(${180 + h * 60}, 70%, 60%)`,
                speed: 0.02 + h * 0.01
            };
            
            // Generate helix points
            for (let i = 0; i < helix.segments; i++) {
                const angle1 = (i / helix.segments) * Math.PI * 8; // 4 full rotations
                const angle2 = angle1 + Math.PI; // Opposite side
                const y = (i / helix.segments) * helix.height - helix.height / 2;
                
                helix.points.push({
                    strand1: {
                        x: Math.cos(angle1) * helix.radius,
                        y: y,
                        z: Math.sin(angle1) * helix.radius,
                        angle: angle1
                    },
                    strand2: {
                        x: Math.cos(angle2) * helix.radius,
                        y: y,
                        z: Math.sin(angle2) * helix.radius,
                        angle: angle2
                    }
                });
                
                // Create connections between strands
                if (i % 8 === 0) { // Connection every 8 segments
                    helix.connections.push(i);
                }
            }
            
            this.helixes.push(helix);
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
    
    project3D(x, y, z, centerX, centerY) {
        const perspective = 800;
        const scale = perspective / (perspective + z);
        return {
            x: centerX + x * scale,
            y: centerY + y * scale,
            scale: scale
        };
    }
    
    drawHelix(helix) {
        const { x, y, points, connections, color1, color2 } = helix;
        
        // Mouse interaction
        const mouseDistance = Math.sqrt(
            Math.pow(this.mouse.x - x, 2) + Math.pow(this.mouse.y - y, 2)
        );
        const mouseEffect = Math.max(0, 1 - mouseDistance / 200);
        
        // Draw connections first (behind strands)
        this.ctx.strokeStyle = `rgba(255, 255, 255, ${0.3 + mouseEffect * 0.3})`;
        this.ctx.lineWidth = 2;
        
        connections.forEach(connectionIndex => {
            if (connectionIndex < points.length) {
                const point = points[connectionIndex];
                const proj1 = this.project3D(
                    point.strand1.x, 
                    point.strand1.y, 
                    point.strand1.z, 
                    x, y
                );
                const proj2 = this.project3D(
                    point.strand2.x, 
                    point.strand2.y, 
                    point.strand2.z, 
                    x, y
                );
                
                this.ctx.beginPath();
                this.ctx.moveTo(proj1.x, proj1.y);
                this.ctx.lineTo(proj2.x, proj2.y);
                this.ctx.stroke();
            }
        });
        
        // Draw strand 1
        this.ctx.strokeStyle = color1;
        this.ctx.lineWidth = 4;
        this.ctx.beginPath();
        
        for (let i = 0; i < points.length; i++) {
            const point = points[i];
            const projected = this.project3D(
                point.strand1.x, 
                point.strand1.y, 
                point.strand1.z, 
                x, y
            );
            
            if (i === 0) {
                this.ctx.moveTo(projected.x, projected.y);
            } else {
                this.ctx.lineTo(projected.x, projected.y);
            }
            
            // Draw nucleotide
            this.ctx.fillStyle = color1;
            this.ctx.beginPath();
            this.ctx.arc(projected.x, projected.y, projected.scale * 3 + mouseEffect * 2, 0, Math.PI * 2);
            this.ctx.fill();
        }
        this.ctx.stroke();
        
        // Draw strand 2
        this.ctx.strokeStyle = color2;
        this.ctx.lineWidth = 4;
        this.ctx.beginPath();
        
        for (let i = 0; i < points.length; i++) {
            const point = points[i];
            const projected = this.project3D(
                point.strand2.x, 
                point.strand2.y, 
                point.strand2.z, 
                x, y
            );
            
            if (i === 0) {
                this.ctx.moveTo(projected.x, projected.y);
            } else {
                this.ctx.lineTo(projected.x, projected.y);
            }
            
            // Draw nucleotide
            this.ctx.fillStyle = color2;
            this.ctx.beginPath();
            this.ctx.arc(projected.x, projected.y, projected.scale * 3 + mouseEffect * 2, 0, Math.PI * 2);
            this.ctx.fill();
        }
        this.ctx.stroke();
    }
    
    animate() {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.time += 0.01;
        
        this.helixes.forEach((helix, helixIndex) => {
            // Rotate the helix
            helix.points.forEach(point => {
                point.strand1.angle += helix.speed;
                point.strand2.angle += helix.speed;
                
                point.strand1.x = Math.cos(point.strand1.angle) * helix.radius;
                point.strand1.z = Math.sin(point.strand1.angle) * helix.radius;
                
                point.strand2.x = Math.cos(point.strand2.angle) * helix.radius;
                point.strand2.z = Math.sin(point.strand2.angle) * helix.radius;
            });
            
            // Add floating motion
            helix.y = this.canvas.height / 2 + Math.sin(this.time + helixIndex) * 50;
            
            this.drawHelix(helix);
        });
        
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('dna-canvas');
    if (canvas) {
        new DNAHelix(canvas);
    }
});