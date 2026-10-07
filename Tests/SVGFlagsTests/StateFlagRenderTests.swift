#if canImport(AppKit)
import AppKit
import XCTest

/// Renders every subdivision flag through AppKit, which draws SVG with
/// CoreSVG: the renderer behind asset catalogs, UIImage and
/// SDWebImageSVGCoder. Browsers draw some SVG that CoreSVG silently drops
/// (a clip path id colliding with a gradient id once blanked whole flags), so
/// a file that looks right on the web can still render empty in an app.
final class StateFlagRenderTests: XCTestCase {

    private static let size = 128

    /// Flags whose shape is deliberately not a full circle or square.
    private static let shapedFlags: Set<String> = [
        "us-oh"  // Ohio's swallowtail burgee leaves a notch on the fly side
    ]

    private static let repoRoot = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent()  // SVGFlagsTests
        .deletingLastPathComponent()  // Tests
        .deletingLastPathComponent()  // package root

    func test_circleStateFlagsRenderAsFullCircles() throws {
        try checkVariant("circle", expectedCoverage: Double.pi / 4)
    }

    func test_squareStateFlagsRenderAsFullSquares() throws {
        try checkVariant("square", expectedCoverage: 1)
    }

    private func checkVariant(_ variant: String, expectedCoverage: Double) throws {
        let folder = Self.repoRoot.appendingPathComponent(variant).appendingPathComponent("states")
        let files = try FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "svg" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
        XCTAssertFalse(files.isEmpty, "no flags found in \(folder.path)")

        for file in files {
            let code = file.deletingPathExtension().lastPathComponent
            guard let stats = Self.render(file) else {
                XCTFail("\(variant)/states/\(code).svg: CoreSVG could not load it")
                continue
            }
            if !Self.shapedFlags.contains(code) {
                XCTAssertEqual(stats.coverage, expectedCoverage, accuracy: 0.01,
                               "\(variant)/states/\(code).svg covers \(stats.coverage) of its frame")
            }
            XCTAssertLessThan(stats.dominantShare, 0.98,
                              "\(variant)/states/\(code).svg renders as nearly a single color")
        }
    }

    private struct RenderStats {
        /// Share of pixels that are mostly opaque.
        let coverage: Double
        /// Share of the opaque pixels taken by the most common color, ignoring
        /// the grey border. A flag whose artwork failed to draw is one color.
        let dominantShare: Double
    }

    private static func render(_ file: URL) -> RenderStats? {
        guard let image = NSImage(contentsOf: file),
              let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size,
                                         bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                                         colorSpaceName: .deviceRGB, bytesPerRow: size * 4, bitsPerPixel: 32),
              let data = rep.bitmapData
        else { return nil }
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
        image.draw(in: NSRect(x: 0, y: 0, width: size, height: size))
        NSGraphicsContext.restoreGraphicsState()

        var opaque = 0
        var counts: [UInt32: Int] = [:]
        for index in stride(from: 0, to: size * size * 4, by: 4) {
            guard data[index + 3] > 127 else { continue }
            opaque += 1
            // Quantize to 32 levels per channel so antialiasing does not
            // count as extra colors.
            let r = UInt32(data[index] >> 3), g = UInt32(data[index + 1] >> 3), b = UInt32(data[index + 2] >> 3)
            let isBorderGrey = abs(Int(data[index]) - 0xCD) < 12 && abs(Int(data[index + 1]) - 0xCF) < 12
                && abs(Int(data[index + 2]) - 0xD3) < 12
            if !isBorderGrey {
                counts[r << 10 | g << 5 | b, default: 0] += 1
            }
        }
        let counted = counts.values.reduce(0, +)
        return RenderStats(coverage: Double(opaque) / Double(size * size),
                           dominantShare: counted == 0 ? 1 : Double(counts.values.max() ?? 0) / Double(counted))
    }
}
#endif
