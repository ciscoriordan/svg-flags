import XCTest
@testable import SVGFlags

private struct StubLocation: FlagLocatable {
    var name: String
    var region: String?
    var country: String?
    var countryCode: String?
    var nativeName: String
    var nativeRegion: String?
    var nativeCountry: String?

    init(
        name: String,
        region: String? = nil,
        country: String? = nil,
        countryCode: String? = nil,
        nativeName: String? = nil,
        nativeRegion: String? = nil,
        nativeCountry: String? = nil
    ) {
        self.name = name
        self.region = region
        self.country = country
        self.countryCode = countryCode
        self.nativeName = nativeName ?? name
        self.nativeRegion = nativeRegion ?? region
        self.nativeCountry = nativeCountry ?? country
    }
}

final class FlagResolverTests: XCTestCase {

    override func setUp() {
        super.setUp()
        SVGFlags.config = .init()
    }

    func test_bundledFlagsIsNonEmpty_andCoversCoreCountries() {
        XCTAssertFalse(FlagResolver.bundledFlags.isEmpty)
        XCTAssertTrue(FlagResolver.bundledFlags.contains("us"))
        XCTAssertTrue(FlagResolver.bundledFlags.contains("gb"))
    }

    /// Guards against drift: every name in `bundledFlags` must have a matching
    /// imageset in the asset catalog, and every imageset in the catalog must be
    /// listed in `bundledFlags`. Reads the catalog off disk via Bundle.module.
    func test_bundledFlagsMatchesAssetCatalogContents() throws {
        let url = try XCTUnwrap(
            Bundle.module.url(forResource: "Flags", withExtension: "xcassets"),
            "Flags.xcassets must ship as a package resource"
        )
        let entries = try FileManager.default.contentsOfDirectory(atPath: url.path)
        let onDisk: Set<String> = Set(
            entries
                .filter { $0.hasSuffix(".imageset") }
                .map { String($0.dropLast(".imageset".count)) }
        )
        XCTAssertEqual(
            onDisk, FlagResolver.bundledFlags,
            "Drift between bundledFlags and asset catalog. Missing from catalog: \(FlagResolver.bundledFlags.subtracting(onDisk)). Extra in catalog: \(onDisk.subtracting(FlagResolver.bundledFlags))."
        )
    }

    func test_countryCode_resolvesBundled() {
        // "Anytown, USA" — no city/state hit, just country code.
        let loc = StubLocation(name: "Anytown", countryCode: "US")
        XCTAssertEqual(FlagResolver.source(for: loc), .bundled("us"))
    }

    func test_countryNameFallback_unitedStates() {
        let loc = StubLocation(name: "Somewhere", country: "United States")
        XCTAssertEqual(FlagResolver.source(for: loc), .bundled("us"))
    }

    func test_countryNameFallback_alias_uk() {
        let loc = StubLocation(name: "London", country: "UK")
        XCTAssertEqual(FlagResolver.source(for: loc), .bundled("gb"))
    }

    func test_remoteCountry_whenNotBundled() {
        // Iceland (`is`) is in the public CDN but is not in the bundled set.
        let loc = StubLocation(name: "Reykjavík", countryCode: "IS")
        let source = FlagResolver.source(for: loc)
        guard case .remote(let folder, let name, let url) = source else {
            return XCTFail("Expected .remote for IS, got \(source)")
        }
        XCTAssertEqual(folder, "countries")
        XCTAssertEqual(name, "is")
        XCTAssertEqual(url.absoluteString, "https://cdn.jsdelivr.net/gh/ciscoriordan/svg-flags@main/circle/countries/is.svg")
    }

    func test_stateLookup_directCode() {
        let loc = StubLocation(name: "Buffalo", region: "NY", countryCode: "US")
        guard case .remote(let folder, let name, _) = FlagResolver.source(for: loc) else {
            return XCTFail("Expected remote state asset")
        }
        XCTAssertEqual(folder, "states")
        XCTAssertEqual(name, "us-ny")
    }

    func test_stateLookup_jsonMap() {
        let loc = StubLocation(name: "Vancouver-suburb", region: "British Columbia", countryCode: "CA")
        // Direct city match should miss (Vancouver-suburb is not in cityMap), but state should hit.
        let source = FlagResolver.source(for: loc)
        guard case .remote(let folder, let name, _) = source else {
            return XCTFail("Expected remote ca-bc, got \(source)")
        }
        XCTAssertEqual(folder, "states")
        XCTAssertEqual(name, "ca-bc")
    }

    func test_cityLookup_vancouver() {
        let loc = StubLocation(name: "Vancouver", region: "British Columbia", countryCode: "CA")
        XCTAssertEqual(FlagResolver.source(for: loc), .bundled("cavan"))
    }

    func test_cityLookup_newYork_bundled() {
        let loc = StubLocation(name: "New York", region: "NY", countryCode: "US")
        XCTAssertEqual(FlagResolver.source(for: loc), .bundled("usnyc"))
    }

    func test_fallback_whenNothingMatches() {
        let loc = StubLocation(name: "Mystery")
        XCTAssertEqual(FlagResolver.source(for: loc), .fallback)
    }

    func test_cdnBaseOverride_isHonoredByRemoteURL() {
        SVGFlags.configure(cdnBase: URL(string: "https://example.com/flags")!)
        let loc = StubLocation(name: "Reykjavík", countryCode: "IS")
        guard case .remote(_, _, let url) = FlagResolver.source(for: loc) else {
            return XCTFail("Expected remote")
        }
        XCTAssertEqual(url.absoluteString, "https://example.com/flags/countries/is.svg")
    }

    func test_bundledOverride_promotesRemoteToBundled() {
        SVGFlags.configure(bundledFlagOverrides: ["is"])
        let loc = StubLocation(name: "Reykjavík", countryCode: "IS")
        XCTAssertEqual(FlagResolver.source(for: loc), .bundled("is"))
    }
}

final class FlagBundleResourcesTests: XCTestCase {
    func test_cityFlagMap_loadsAndHasEntries() throws {
        let url = try XCTUnwrap(Bundle.module.url(forResource: "cityFlagMap", withExtension: "json"))
        let data = try Data(contentsOf: url)
        struct File: Decodable { let version: Int; let entries: [String: String] }
        let decoded = try JSONDecoder().decode(File.self, from: data)
        XCTAssertGreaterThan(decoded.entries.count, 0)
        XCTAssertNotNil(decoded.entries["ca:vancouver"])
    }

    func test_subdivisionMap_loadsAndHasEntries() throws {
        let url = try XCTUnwrap(Bundle.module.url(forResource: "subdivisionMap", withExtension: "json"))
        let data = try Data(contentsOf: url)
        struct File: Decodable { let version: Int; let entries: [String: String] }
        let decoded = try JSONDecoder().decode(File.self, from: data)
        XCTAssertGreaterThan(decoded.entries.count, 0)
        XCTAssertEqual(decoded.entries["us:california"], "us-ca")
    }
}

final class FlagSVGStripperTests: XCTestCase {
    func test_stripBorder_removesMarkerCircle() {
        let input = """
        <svg xmlns="http://www.w3.org/2000/svg" width="512" height="512">
        <g><rect width="512" height="512" fill="#ff0000"/></g>
        <!-- border --><circle cx="256" cy="256" r="256" fill="none" stroke="#cdcfd3" stroke-width="16"/>
        </svg>
        """
        let data = Data(input.utf8)
        let out = FlagSVGStripper.stripBorder(from: data)
        let outString = String(decoding: out, as: UTF8.self)
        XCTAssertFalse(outString.contains("<!-- border -->"))
        XCTAssertFalse(outString.contains("stroke=\"#cdcfd3\""))
        XCTAssertTrue(outString.contains("<rect width=\"512\""))
    }

    func test_stripBorder_leavesUnrelatedCircleAlone() {
        let input = """
        <svg><circle cx="10" cy="10" r="5" fill="red"/></svg>
        """
        let data = Data(input.utf8)
        let out = FlagSVGStripper.stripBorder(from: data)
        XCTAssertEqual(out, data)
    }
}
