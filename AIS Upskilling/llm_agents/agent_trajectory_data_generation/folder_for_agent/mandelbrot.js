const canvas = document.getElementById('mandelbrotCanvas');
const ctx = canvas.getContext('2d');

let width, height;

function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
}

window.addEventListener('resize', resize);
resize();

function mandelbrot(c_re, c_im, max_iter) {
    let z_re = c_re, z_im = c_im;
    let n;
    for (n = 0; n < max_iter; ++n) {
        let z_re2 = z_re*z_re, z_im2 = z_im*z_im;
        if (z_re2 + z_im2 > 4.0) break;
        let new_re = z_re2 - z_im2 + c_re;
        let new_im = 2*z_re*z_im + c_im;
        z_re = new_re;
        z_im = new_im;
    }
    
    if (n === max_iter) return max_iter;
    return n + 1 - Math.log(Math.log(Math.sqrt(z_re*z_re + z_im*z_im)))/Math.log(2);
}

function getColor(iter, max_iter) {
    let t = iter / max_iter;
    let r = Math.floor(9*(1-t)*t*t*t*255);
    let g = Math.floor(15*(1-t)*(1-t)*t*t*255);
    let b = Math.floor(8.5*(1-t)*(1-t)*(1-t)*t*255);
    return [r, g, b];
}

let max_iter = 100;
let zoom = 1;
let moveX = 0;
let moveY = 0;
let time = 0;

function draw() {
    let imageData = ctx.createImageData(width, height);
    let data = imageData.data;

    // Animate movement over time
    moveX = 0.5 * Math.sin(time * 0.3);
    moveY = 0.5 * Math.cos(time * 0.3);
    zoom = 1 + 0.5 * Math.sin(time * 0.1);

    for (let x = 0; x < width; x++) {
        for (let y = 0; y < height; y++) {
            // Scale pixel to complex plane
            let c_re = (x - width/2) * 4/width / zoom + moveX;
            let c_im = (y - height/2) * 4/width / zoom + moveY;

            let iter = mandelbrot(c_re, c_im, max_iter);
            let color = getColor(iter, max_iter);

            let idx = (y * width + x) * 4;
            data[idx] = color[0];
            data[idx + 1] = color[1];
            data[idx + 2] = color[2];
            data[idx + 3] = 255;
        }
    }

    ctx.putImageData(imageData, 0, 0);
    time += 0.03;
    requestAnimationFrame(draw);
}

draw();
