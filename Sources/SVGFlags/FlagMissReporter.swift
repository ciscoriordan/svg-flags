import Foundation

/// In-process dedup wrapper around the configured `missReporter`. Each
/// `(folder, name)` is reported at most once per app lifetime — so a missing
/// CDN asset never produces a runaway stream of identical reports.
enum FlagMissReporter {
    private static let lock = NSLock()
    private nonisolated(unsafe) static var reported: Set<String> = []

    static func report<L: FlagLocatable>(folder: String, name: String, location: L) {
        guard let reporter = SVGFlags.config.missReporter else { return }

        let key = "\(folder)/\(name)"
        lock.lock()
        let already = reported.contains(key)
        if !already { reported.insert(key) }
        lock.unlock()
        if already { return }

        let miss = FlagMiss(
            folder: folder,
            name: name,
            countryCode: location.countryCode?.isEmpty == false ? location.countryCode?.lowercased() : nil,
            region: (location.region?.isEmpty == false) ? location.region : nil,
            city: location.name.isEmpty ? nil : location.name
        )
        reporter(miss)
    }
}
