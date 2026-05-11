import Foundation

/// Top-level namespace for package configuration. Holds the CDN URL the
/// resolver targets, any consumer-supplied additions to `bundledFlags`, and
/// the optional miss-reporter the `FlagView` should call on remote 404s.
///
/// Configure once near app launch:
/// ```swift
/// SVGFlags.configure(
///     cdnBase: URL(string: "https://cdn.jsdelivr.net/gh/ciscoriordan/svg-flags@main/circle")!,
///     bundledFlagOverrides: ["mycity"],
///     missReporter: { miss in MyTelemetry.report(miss) }
/// )
/// SVGFlags.installSVGBorderStripper()
/// ```
public enum SVGFlags {
    /// Default CDN base. Points to jsDelivr's mirror of the public svg-flags
    /// repository's `circle` directory. Trailing `circle` is required; the
    /// resolver appends `/{folder}/{name}.svg`.
    public static let defaultCDNBase = URL(string: "https://cdn.jsdelivr.net/gh/ciscoriordan/svg-flags@main/circle")!

    /// Current, effective configuration. Reads are safe from any thread; writes
    /// should happen from the main actor at launch.
    public static var config: Config {
        get { lock.withLock { _config } }
        set { lock.withLock { _config = newValue } }
    }

    /// Convenience for the common "set everything at once" call site. Any
    /// argument left as `nil` keeps its current value.
    public static func configure(
        cdnBase: URL? = nil,
        bundledFlagOverrides: Set<String>? = nil,
        missReporter: (@Sendable (FlagMiss) -> Void)? = nil
    ) {
        lock.withLock {
            if let cdnBase { _config.cdnBase = cdnBase }
            if let bundledFlagOverrides { _config.bundledFlagOverrides = bundledFlagOverrides }
            if let missReporter { _config.missReporter = missReporter }
        }
    }

    /// Install the SVG border-stripper into SDWebImage's downloader so remotely
    /// fetched flags visually match the bundled ones (which have the
    /// `<!-- border --><circle .../>` element pre-stripped). Idempotent — safe
    /// to call once at app launch, or multiple times.
    @MainActor
    public static func installSVGBorderStripper() {
        FlagSVGStripper.install()
    }

    public struct Config: Sendable {
        public var cdnBase: URL
        /// Extra asset names a consumer ships in their own bundle. The
        /// package's own bundled set is read off the asset catalog; this is
        /// for consumers that want to layer extra bundled imagesets on top.
        public var bundledFlagOverrides: Set<String>
        public var missReporter: (@Sendable (FlagMiss) -> Void)?

        public init(
            cdnBase: URL = SVGFlags.defaultCDNBase,
            bundledFlagOverrides: Set<String> = [],
            missReporter: (@Sendable (FlagMiss) -> Void)? = nil
        ) {
            self.cdnBase = cdnBase
            self.bundledFlagOverrides = bundledFlagOverrides
            self.missReporter = missReporter
        }
    }

    // MARK: - Private

    private static let lock = NSLock()
    private nonisolated(unsafe) static var _config = Config()
}

private extension NSLock {
    func withLock<T>(_ body: () -> T) -> T {
        lock()
        defer { unlock() }
        return body()
    }
}
