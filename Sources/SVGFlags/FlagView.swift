import SwiftUI
import SDWebImage
import SDWebImageSwiftUI

/// Drop-in circular flag for any `FlagLocatable`. Resolution order is
/// city → state → country → globe; bundled assets render off the package
/// bundle, anything else streams off the configured CDN through SDWebImage.
/// When the CDN has no flag at a streamed URL (a state without a flag, for
/// example), the view moves on to the next source, so a missing state flag
/// shows the country flag rather than the globe. A failure that may go away
/// (offline, timeout, server error) keeps the source, and SDWebImage loads it
/// again the next time the flag appears.
public struct FlagView<L: FlagLocatable>: View {
    private let location: L
    private let size: CGFloat
    /// Remote flags the CDN does not have, or that cannot be drawn.
    @State private var missingURLs: Set<URL> = []

    public init(for location: L, size: CGFloat = 24) {
        self.location = location
        self.size = size
    }

    public var body: some View {
        Group {
            switch FlagResolver.source(for: location, skipping: missingURLs) {
            case .bundled(let name):
                Image("Flags/\(name)", bundle: .module)
                    .resizable()
                    .scaledToFill()
            case .remote(let folder, let name, let url):
                WebImage(url: url) { image in
                    image
                        .resizable()
                        .scaledToFill()
                } placeholder: {
                    globe
                }
                .onFailure { error in
                    // SDWebImage delivers completions on the main queue.
                    guard FlagLoadFailure.isMissingFlag(error) else { return }
                    missingURLs.insert(url)
                    guard FlagLoadFailure.statusCode(of: error) == 404 else { return }
                    FlagMissReporter.report(folder: folder, name: name, location: location)
                }
                // A new identity per URL, so moving on to the next source
                // starts a fresh download instead of reusing this one.
                .id(url)
            case .fallback:
                globe
            }
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
        .accessibilityHidden(true)
    }

    private var globe: some View {
        Image(systemName: "globe")
            .resizable()
            .scaledToFit()
            .foregroundStyle(.secondary)
            .padding(2)
    }
}

/// Sorts a failed flag download into a missing flag, after which `FlagView`
/// moves on to the next source for good, and a failure that may go away,
/// after which it keeps the source.
///
/// A source given up on stays skipped for the lifetime of the view, so only
/// failures that loading again cannot fix count as missing. Being offline,
/// a timeout, a lost connection or a server error must not count: the row
/// would otherwise stay on the country flag (or the globe, for a country
/// that is streamed too) after the connection comes back, and SDWebImage
/// already retries those when the flag appears again.
enum FlagLoadFailure {
    static func isMissingFlag(_ error: Error) -> Bool {
        let nsError = error as NSError
        guard nsError.domain == SDWebImageErrorDomain else {
            // URLSession errors are left to SDWebImage. It retries the ones
            // that may go away; it blocks the others, and its next attempt
            // then fails as blackListed, which counts below.
            return false
        }
        switch SDWebImageError.Code(rawValue: nsError.code) {
        case .invalidDownloadStatusCode:
            // The CDN answered. A client error (404 for a file that is not
            // there) is final, except a request timeout or rate limit; a
            // server error is not.
            guard let status = statusCode(of: error) else { return false }
            return (400..<500).contains(status) && status != 408 && status != 429
        case .badImageData, .invalidURL:
            // The file is empty or cannot be decoded, or the URL is not
            // valid; downloading it again gives the same result.
            return true
        case .blackListed:
            // SDWebImage has marked the URL as failing for good and will not
            // request it again in this process, so staying would leave the
            // globe up.
            return true
        default:
            return false
        }
    }

    /// The HTTP status of a failed download, if the server answered.
    static func statusCode(of error: Error) -> Int? {
        (error as NSError).userInfo[SDWebImageErrorDownloadStatusCodeKey] as? Int
    }
}
