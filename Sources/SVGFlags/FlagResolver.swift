import Foundation

/// City → state → country → globe resolver. Returns a `FlagSource` describing
/// where the renderer should pull the artwork from.
public enum FlagResolver {

    /// Resolve to a renderable source. Pure function, safe to call off the
    /// main actor.
    public static func source<L: FlagLocatable>(for location: L) -> FlagSource {
        if let asset = cityAsset(for: location) {
            return resolved(asset: asset, folder: "cities")
        }
        if let asset = stateAsset(for: location) {
            return resolved(asset: asset, folder: "states")
        }
        if let asset = countryAsset(for: location) {
            return resolved(asset: asset, folder: "countries")
        }
        return .fallback
    }

    /// Asset basenames available in the package's bundled `Flags` catalog.
    /// At build time the asset catalog ships the imagesets listed below — kept
    /// in sync via `Tests/SVGFlagsTests` (the catalog is scanned on disk during
    /// the test run and asserted equal to this set). Consumers can layer extra
    /// bundled flags on top via `SVGFlags.Config.bundledFlagOverrides`.
    public static let bundledFlags: Set<String> = [
        // Language-locale countries (covers en/es/de/fr/it/pt/ja/ko/zh/el).
        "us", "ca", "gb", "au", "nz", "ie", "za",
        "es", "mx", "ar", "co", "pe", "cl", "ve", "cu",
        "de", "at", "ch", "li",
        "fr", "be", "lu", "mc",
        "it", "sm",
        "pt", "br", "ao", "mz",
        "jp", "kr",
        "cn", "sg",
        "gr", "cy",

        // City flags currently bundled in our asset catalog.
        "cavan", "esbcn", "usnyc"
    ]

    // MARK: - Private resolution

    private static func resolved(asset: String, folder: String) -> FlagSource {
        let effectiveBundled = bundledFlags.union(SVGFlags.config.bundledFlagOverrides)
        if effectiveBundled.contains(asset) {
            return .bundled(asset)
        }
        let base = SVGFlags.config.cdnBase
        let url = base.appendingPathComponent(folder).appendingPathComponent("\(asset).svg")
        return .remote(folder: folder, name: asset, url: url)
    }

    // MARK: - City

    private static let cityMap: [String: String] = {
        loadMap(resource: "cityFlagMap")
    }()

    private static func cityAsset<L: FlagLocatable>(for location: L) -> String? {
        let cc = resolvedCountryCode(for: location)
        guard !cc.isEmpty else { return nil }
        for candidate in [location.nativeName, location.name] {
            let key = "\(cc):\(normalize(candidate))"
            if let asset = cityMap[key] { return asset }
        }
        return nil
    }

    // MARK: - State / subdivision

    private static let subdivisionMap: [String: String] = {
        loadMap(resource: "subdivisionMap")
    }()

    private static func stateAsset<L: FlagLocatable>(for location: L) -> String? {
        let cc = resolvedCountryCode(for: location).lowercased()
        guard !cc.isEmpty else { return nil }

        for candidate in [location.nativeRegion, location.region] {
            guard let raw = candidate?.trimmingCharacters(in: .whitespaces), !raw.isEmpty else { continue }
            // Direct subdivision code (2–3 letters): "BC", "NY", "ENG".
            if raw.count <= 3, raw.allSatisfy(\.isLetter) {
                return "\(cc)-\(raw.lowercased())"
            }
            let key = "\(cc):\(raw.lowercased())"
            if let asset = subdivisionMap[key] { return asset }
        }
        return nil
    }

    // MARK: - Country

    private static func countryAsset<L: FlagLocatable>(for location: L) -> String? {
        let cc = resolvedCountryCode(for: location)
        return cc.isEmpty ? nil : cc
    }

    private static func resolvedCountryCode<L: FlagLocatable>(for location: L) -> String {
        if let explicit = location.countryCode?.lowercased(), !explicit.isEmpty {
            return explicit
        }
        for candidate in [location.nativeCountry, location.country] {
            if let name = candidate?.lowercased(), let code = countryNameToCode[name] {
                return code
            }
        }
        return ""
    }

    private static let countryNameToCode: [String: String] = {
        var map: [String: String] = [:]
        for region in Locale.Region.isoRegions {
            let id = region.identifier
            if let name = Locale(identifier: "en_US").localizedString(forRegionCode: id) {
                map[name.lowercased()] = id.lowercased()
            }
        }
        // Common aliases not covered by Locale's canonical names.
        map["usa"] = "us"
        map["u.s.a."] = "us"
        map["united states of america"] = "us"
        map["uk"] = "gb"
        map["britain"] = "gb"
        map["great britain"] = "gb"
        map["south korea"] = "kr"
        map["north korea"] = "kp"
        map["czech republic"] = "cz"
        map["czechia"] = "cz"
        map["myanmar"] = "mm"
        map["burma"] = "mm"
        map["ivory coast"] = "ci"
        map["cape verde"] = "cv"
        map["east timor"] = "tl"
        map["swaziland"] = "sz"
        map["macedonia"] = "mk"
        map["north macedonia"] = "mk"
        return map
    }()

    // MARK: - Helpers

    private struct MapFile: Decodable {
        let version: Int
        let entries: [String: String]
    }

    private static func loadMap(resource: String) -> [String: String] {
        guard let url = Bundle.module.url(forResource: resource, withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let decoded = try? JSONDecoder().decode(MapFile.self, from: data) else {
            return [:]
        }
        return decoded.entries
    }

    private static func normalize(_ value: String) -> String {
        value.lowercased().trimmingCharacters(in: .whitespaces)
    }
}
