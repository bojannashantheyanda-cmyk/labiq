from PIL import Image, ImageDraw
import math

def create_labiq_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    images = []
    
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Blue rounded square background
        radius = size // 6
        draw.rounded_rectangle([0, 0, size-1, size-1], radius=radius, fill=(26, 86, 160, 255))
        
        pad = size // 6
        chart_x = pad
        chart_y = pad
        chart_w = size - pad * 2
        chart_h = size - pad * 2
        
        # Three bars
        bar_w = int(chart_w * 0.18)
        gap = int(chart_w * 0.08)
        bottom = chart_y + chart_h
        
        bar_heights = [0.45, 0.65, 0.85]
        bar_colors = [(255,255,255,120), (255,255,255,180), (255,255,255,255)]
        
        bars_x = []
        for i, (bh, bc) in enumerate(zip(bar_heights, bar_colors)):
            bx = chart_x + i * (bar_w + gap) + gap
            by = bottom - int(chart_h * bh)
            br = max(2, bar_w // 4)
            draw.rounded_rectangle([bx, by, bx+bar_w, bottom], radius=br, fill=bc)
            bars_x.append((bx + bar_w // 2, by))
        
        # Trend line
        if size >= 32:
            lw = max(1, size // 32)
            for i in range(len(bars_x)-1):
                x1, y1 = bars_x[i]
                x2, y2 = bars_x[i+1]
                draw.line([x1, y1, x2, y2], fill=(96, 184, 255, 255), width=lw)
            
            # Dot at end
            dot_r = max(2, size // 20)
            ex, ey = bars_x[-1]
            draw.ellipse([ex-dot_r, ey-dot_r, ex+dot_r, ey+dot_r], fill=(96, 184, 255, 255))
        
        images.append(img)
    
    # Save as .ico
    images[0].save(
        'labiq.ico',
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print("labiq.ico created successfully!")

create_labiq_icon()