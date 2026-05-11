import Foundation
import SDWebImage

/// Strips the `<!-- border --><circle .../>` element from incoming SVG bytes so
/// remotely-fetched flags match the bundled assets visually (the bundled set is
/// pre-stripped). Hooked into `SDWebImageDownloader` so it runs once per
/// download. Opt in via `SVGFlags.installBorderStripper()` at launch.
enum FlagSVGStripper {
    @MainActor
    static func install() {
        SDWebImageDownloader.shared.decryptor = SDWebImageDownloaderDecryptor { data, response in
            guard isSVG(response: response, data: data) else { return data }
            return stripBorder(from: data)
        }
    }

    /// Internal — exposed for tests.
    static func stripBorder(from data: Data) -> Data {
        guard let text = String(data: data, encoding: .utf8) else { return data }
        let stripped = borderRegex.stringByReplacingMatches(
            in: text,
            range: NSRange(text.startIndex..., in: text),
            withTemplate: ""
        )
        return stripped.data(using: .utf8) ?? data
    }

    private static let borderRegex: NSRegularExpression = {
        let pattern = ##"[ \t]*<!--\s*border\s*-->\s*<circle\b[^/]*?stroke\s*=\s*"#cdcfd3"[^/]*/>\s*\n?"##
        // Pattern is a static literal we control — force-try is acceptable here.
        return try! NSRegularExpression(pattern: pattern, options: [.caseInsensitive])
    }()

    private static func isSVG(response: URLResponse?, data: Data) -> Bool {
        if let mime = response?.mimeType?.lowercased(), mime.contains("svg") {
            return true
        }
        if let url = response?.url, url.pathExtension.lowercased() == "svg" {
            return true
        }
        let prefix = data.prefix(256)
        if let head = String(data: prefix, encoding: .utf8)?.lowercased(),
           head.contains("<svg") {
            return true
        }
        return false
    }
}
