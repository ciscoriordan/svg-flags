// Renders SVG files to PNG through AppKit, which draws SVG with CoreSVG: the
// same renderer Xcode asset catalogs, UIImage and SDWebImageSVGCoder use.
// Browsers and rsvg accept SVG features that CoreSVG silently skips, so the
// pipeline compares both renders to catch artwork that would break in an app.
//
// Reads jobs from standard input, one tab-separated line each:
//   <svg> <png> <width> <height>
// Prints "ok <png>" or "fail <svg>" for each job.
import AppKit

while let line = readLine() {
    let parts = line.split(separator: "\t").map(String.init)
    guard parts.count == 4, let width = Int(parts[2]), let height = Int(parts[3]) else { continue }
    let (input, output) = (parts[0], parts[1])
    guard let image = NSImage(contentsOf: URL(fileURLWithPath: input)),
          let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: width, pixelsHigh: height,
                                     bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                                     colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0) else {
        print("fail \(input)")
        continue
    }
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    image.draw(in: NSRect(x: 0, y: 0, width: width, height: height))
    NSGraphicsContext.restoreGraphicsState()
    guard let png = rep.representation(using: .png, properties: [:]) else {
        print("fail \(input)")
        continue
    }
    try? png.write(to: URL(fileURLWithPath: output))
    print("ok \(output)")
}
