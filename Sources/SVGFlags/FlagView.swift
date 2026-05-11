import SwiftUI
import SDWebImage
import SDWebImageSwiftUI

/// Drop-in circular flag for any `FlagLocatable`. Resolution order is
/// city → state → country → globe; bundled assets render off the package
/// bundle, anything else streams off the configured CDN through SDWebImage.
public struct FlagView<L: FlagLocatable>: View {
    private let location: L
    private let size: CGFloat

    public init(for location: L, size: CGFloat = 24) {
        self.location = location
        self.size = size
    }

    public var body: some View {
        Group {
            switch FlagResolver.source(for: location) {
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
                    let nsError = error as NSError
                    let status = nsError.userInfo[SDWebImageErrorDownloadStatusCodeKey] as? Int ?? 0
                    guard status == 404 else { return }
                    FlagMissReporter.report(folder: folder, name: name, location: location)
                }
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
