// 3D Wave Background
class Wave3D {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.points = [];
        this.time = 0;
        this.mouse = { x: 0, y: 0 };
        
        this.init();
        this.bindEvents();
        this.animate();
    }
    
    init() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Create grid of points
        this.cols = 50;
        this.rows = 30;
        this.spacing = 20;
        
        for (let i = 0; i < this.cols; i++) {
            this.points[i] = [];
            for (let j = 0; j < this.rows; j++) {
                this.points[i][j] = {
                    x: i * this.spacing - (this.cols * this.spacing) / 2,
                    y: j * this.spacing - (this.rows * this.spacing) / 2,
                    z: 0,
                    originalX: i * this.spacing - (this.cols * this.spacing) / 2,
                    originalY: j * this.spacing - (this.rows * this.spacing) / 2
                };
            }
        }
        
        window.addEventListener('resize', () => {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerHeight;
        });
    }
    
    bindEvents() {
        this.canvas.addEventListener('mousemove', (e) => {
            this.mouse.x = (e.clientX - this.canvas.width / 2) / this.canvas.width * 2;
            this.mouse.y = (e.clientY - this.canvas.height / 2) / this.canvas.height * 2;
        });
    }
    
    project3D(x, y, z) {
        const perspective = 400;
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        const scale = perspective / (perspective + z);
        return {
            x: centerX + x * scale,
            y: centerY + y * scale,
            scale: scale
        };
    }
    
    animate() {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.time += 0.02;
        
        // Update wave points
        for (let i = 0; i < this.cols; i++) {
            for (let j = 0; j < this.rows; j++) {
                const point = this.points[i][j];
                
                // Create wave effect
                const distance = Math.sqrt(
                    Math.pow(point.originalX, 2) + Math.pow(point.originalY, 2)
                );
                
                point.z = Math.sin(distance * 0.01 + this.time) * 50 +
                         Math.sin(point.originalX * 0.01 + this.time * 1.5) * 30 +
                         Math.sin(point.originalY * 0.01 + this.time * 0.8) * 20;
                
                // Mouse interaction
                const mouseDistance = Math.sqrt(
                    Math.pow(point.originalX - this.mouse.x * 200, 2) +
                    Math.pow(point.originalY - this.mouse.y * 200, 2)
                );
                
                if (mouseDistance < 100) {
                    point.z += (100 - mouseDistance) * 2;
                }
            }
        }
        
        // Draw connections
        this.ctx.strokeStyle = 'rgba(100, 150, 255, 0.3)';
        this.ctx.lineWidth = 1;
        
        for (let i = 0; i < this.cols - 1; i++) {
            for (let j = 0; j < this.rows - 1; j++) {
                const point1 = this.project3D(
                    this.points[i][j].x,
                    this.points[i][j].y,
                    this.points[i][j].z
                );
                const point2 = this.project3D(
                    this.points[i + 1][j].x,
                    this.points[i + 1][j].y,
                    this.points[i + 1][j].z
                );
                const point3 = this.project3D(
                    this.points[i][j + 1].x,
                    this.points[i][j + 1].y,
                    this.points[i][j + 1].z
                );
                
                // Draw horizontal line
                this.ctx.beginPath();
                this.ctx.moveTo(point1.x, point1.y);
                this.ctx.lineTo(point2.x, point2.y);
                this.ctx.stroke();
                
                // Draw vertical line
                this.ctx.beginPath();
                this.ctx.moveTo(point1.x, point1.y);
                this.ctx.lineTo(point3.x, point3.y);
                this.ctx.stroke();
            }
        }
        
        // Draw points
        for (let i = 0; i < this.cols; i++) {
            for (let j = 0; j < this.rows; j++) {
                const point = this.project3D(
                    this.points[i][j].x,
                    this.points[i][j].y,
                    this.points[i][j].z
                );
                
                const intensity = (this.points[i][j].z + 100) / 200;
                this.ctx.fillStyle = `rgba(100, 150, 255, ${intensity * 0.8})`;
                this.ctx.beginPath();
                this.ctx.arc(point.x, point.y, point.scale * 2, 0, Math.PI * 2);
                this.ctx.fill();
            }
        }
        
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('waves-canvas');
    if (canvas) {
        new Wave3D(canvas);
    }
});