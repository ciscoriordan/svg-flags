import Foundation

/// Result of resolving a `FlagLocatable` to a renderable flag asset.
public enum FlagSource: Sendable, Equatable {
    /// The asset is shipped inside the package's `Flags` image catalog.
    /// Render via `Image("Flags/<name>", bundle: .module)` if you ever need to
    /// reach into it yourself; otherwise use `FlagView`.
    case bundled(String)

    /// The asset is not bundled; fetch it from the CDN. `folder` is the CDN
    /// sub-directory ("cities" / "states" / "countries"), exposed so callers
    /// can pipe it into miss-reporting / analytics.
    case remote(folder: String, name: String, url: URL)

    /// Nothing matched. Render a globe placeholder.
    case fallback
}

/// Reported once per process (folder, name) the first time the CDN returns 404
/// for that asset. Lets consumers wire the misses into their own telemetry
/// pipeline without the package taking a dependency on any specific backend.
public struct FlagMiss: Sendable, Equatable {
    public let folder: String
    public let name: String
    public let countryCode: String?
    public let region: String?
    public let city: String?

    public init(
        folder: String,
        name: String,
        countryCode: String?,
        region: String?,
        city: String?
    ) {
        self.folder = folder
        self.name = name
        self.countryCode = countryCode
        self.region = region
        self.city = city
    }
}
