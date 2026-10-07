import XCTest
#if canImport(AppKit)
import AppKit
#endif
import SDWebImage
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
    /// listed in `bundledFlags`. SwiftPM compiles the catalog into Assets.car,
    /// so the `.xcassets` folder itself never ships in `Bundle.module`; the
    /// imagesets are read from the package sources instead.
    func test_bundledFlagsMatchesAssetCatalogContents() throws {
        let flagsDir = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()  // SVGFlagsTests
            .deletingLastPathComponent()  // Tests
            .deletingLastPathComponent()  // package root
            .appendingPathComponent("Sources/SVGFlags/Resources/Assets.xcassets/Flags", isDirectory: true)
        let entries = try FileManager.default.contentsOfDirectory(atPath: flagsDir.path)
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

    #if canImport(AppKit)
    /// Every bundled flag loads from the compiled catalog under the `Flags/`
    /// namespace that `FlagView` uses.
    func test_bundledFlagsLoadFromCompiledCatalog() {
        for name in FlagResolver.bundledFlags.sorted() {
            XCTAssertNotNil(Bundle.module.image(forResource: "Flags/\(name)"),
                            "Flags/\(name) is not in the compiled asset catalog")
        }
    }
    #endif

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

    func test_stateLookup_newSubdivisionNamesAndGeocoderAliases() {
        let cases: [(String, String, String)] = [
            ("AR", "Córdoba", "ar-x"),
            ("AR", "Buenos Aires", "ar-b"),
            ("AR", "Ciudad Autónoma de Buenos Aires", "ar-c"),
            ("AR", "Tierra del Fuego", "ar-v"),
            ("BR", "São Paulo", "br-sp"),
            ("BR", "Sao Paulo", "br-sp"),
            ("BR", "Distrito Federal", "br-df"),
            ("BR", "SP", "br-sp"),
            ("CH", "Zürich", "ch-zh"),
            ("CH", "Zurich", "ch-zh"),
            ("CH", "Genève", "ch-ge"),
            ("CH", "Graubünden", "ch-gr"),
            ("CH", "Grigioni", "ch-gr"),
            ("CH", "ZH", "ch-zh"),
            ("MX", "Jalisco", "mx-jal"),
            ("MX", "Jal.", "mx-jal"),
            ("MX", "CDMX", "mx-cmx"),
            ("MX", "Méx.", "mx-mex"),
            ("MX", "México", "mx-mex"),
            ("MX", "Gto", "mx-gua"),
            ("MX", "Gto.", "mx-gua"),
            ("MX", "Qro", "mx-que"),
            ("MX", "NL", "mx-nle"),
            ("MX", "B.C.", "mx-bcn"),
            ("MX", "Q. Roo", "mx-roo"),
            ("MX", "  jAL.  ", "mx-jal")
        ]
        for (country, region, expected) in cases {
            let loc = StubLocation(name: "Unmapped locality", region: region, countryCode: country)
            guard case .remote(let folder, let name, _) = FlagResolver.source(for: loc) else {
                XCTFail("Expected a subdivision for \(country):\(region)")
                continue
            }
            XCTAssertEqual(folder, "states")
            XCTAssertEqual(name, expected, "\(country):\(region)")
        }
    }

    func test_stateLookup_nativeNameHasPriority() {
        let loc = StubLocation(name: "Unmapped locality", region: "Geneva", countryCode: "CH",
                               nativeRegion: "Zürich")
        guard case .remote(_, let name, _) = FlagResolver.source(for: loc) else {
            return XCTFail("Expected a subdivision")
        }
        XCTAssertEqual(name, "ch-zh")
    }

    func test_stateLookup_mexicoCityFallsBackWhenFlagIsMissing() {
        // Mexico City has a recognized subdivision code but no official flag
        // in this collection. Preserve the existing missing-asset fallback.
        let loc = StubLocation(name: "Unmapped locality", region: "CDMX", countryCode: "MX")
        guard case .remote(_, let name, let url) = FlagResolver.source(for: loc) else {
            return XCTFail("Expected Mexico City's subdivision code")
        }
        XCTAssertEqual(name, "mx-cmx")
        XCTAssertEqual(FlagResolver.source(for: loc, skipping: [url]), .bundled("mx"))
    }

    func test_cityLookup_vancouver() {
        let loc = StubLocation(name: "Vancouver", region: "British Columbia", countryCode: "CA")
        XCTAssertEqual(FlagResolver.source(for: loc), .bundled("cavan"))
    }

    func test_cityLookup_newYork_bundled() {
        let loc = StubLocation(name: "New York", region: "NY", countryCode: "US")
        XCTAssertEqual(FlagResolver.source(for: loc), .bundled("usnyc"))
    }

    func test_stateLookup_singleLetterCode() {
        // Argentina's provinces have one-letter ISO 3166-2 codes.
        let loc = StubLocation(name: "Córdoba", region: "X", countryCode: "AR")
        guard case .remote(let folder, let name, _) = FlagResolver.source(for: loc) else {
            return XCTFail("Expected remote state asset")
        }
        XCTAssertEqual(folder, "states")
        XCTAssertEqual(name, "ar-x")
    }

    func test_stateLookup_nonASCIIRegion_isNotUsedAsACode() {
        // Character.isLetter is true for kanji; 東京都 must not become "jp-東京都".
        let loc = StubLocation(name: "新宿区", region: "東京都", countryCode: "JP")
        XCTAssertEqual(FlagResolver.source(for: loc), .bundled("jp"))
        XCTAssertEqual(FlagResolver.sources(for: loc), [.bundled("jp")])
    }

    func test_stateLookup_hangulRegion_isNotUsedAsACode() {
        let loc = StubLocation(name: "강남구", region: "서울", countryCode: "KR")
        XCTAssertEqual(FlagResolver.sources(for: loc), [.bundled("kr")])
    }

    func test_stateLookup_accentedLatinRegion_isNotUsedAsACode() {
        let loc = StubLocation(name: "Somewhere", region: "Ñu", countryCode: "ES")
        XCTAssertEqual(FlagResolver.sources(for: loc), [.bundled("es")])
    }

    func test_stateLookup_regionEqualToCountryCode_isTheCountry() {
        // Singapore reports its region as "SG"; there is no sg-sg flag.
        let loc = StubLocation(name: "Singapore", region: "SG", countryCode: "SG")
        XCTAssertEqual(FlagResolver.sources(for: loc), [.bundled("sg")])
    }

    func test_stateLookup_regionEqualToCountryCode_ignoresCase() {
        let loc = StubLocation(name: "Singapore", region: "sg", countryCode: "SG")
        XCTAssertEqual(FlagResolver.sources(for: loc), [.bundled("sg")])
    }

    func test_sources_listStateThenCountry() {
        let loc = StubLocation(name: "Buffalo", region: "NY", countryCode: "US")
        let sources = FlagResolver.sources(for: loc)
        XCTAssertEqual(sources.count, 2)
        guard case .remote(let folder, let name, _) = sources.first else {
            return XCTFail("Expected the state first, got \(sources)")
        }
        XCTAssertEqual(folder, "states")
        XCTAssertEqual(name, "us-ny")
        XCTAssertEqual(sources.last, .bundled("us"))
    }

    func test_sources_listCityStateCountry() {
        let loc = StubLocation(name: "Vancouver", region: "British Columbia", countryCode: "CA")
        let sources = FlagResolver.sources(for: loc)
        XCTAssertEqual(sources.count, 3)
        XCTAssertEqual(sources.first, .bundled("cavan"))
        XCTAssertEqual(sources.last, .bundled("ca"))
    }

    func test_sources_emptyWhenNothingMatches() {
        XCTAssertEqual(FlagResolver.sources(for: StubLocation(name: "Mystery")), [])
    }

    func test_skippingFailedState_fallsBackToCountry() {
        // A state flag the CDN does not have (404) gives way to the country flag.
        let loc = StubLocation(name: "Monterrey", region: "NLE", countryCode: "MX")
        guard case .remote(_, let name, let url) = FlagResolver.source(for: loc) else {
            return XCTFail("Expected remote state asset")
        }
        XCTAssertEqual(name, "mx-nle")
        XCTAssertEqual(FlagResolver.source(for: loc, skipping: [url]), .bundled("mx"))
    }

    func test_skippingFailedStateAndCountry_fallsBackToGlobe() {
        let loc = StubLocation(name: "Reykjavík", region: "RVK", countryCode: "IS")
        let urls = FlagResolver.sources(for: loc).compactMap { source -> URL? in
            if case .remote(_, _, let url) = source { return url }
            return nil
        }
        XCTAssertEqual(urls.count, 2)
        XCTAssertEqual(FlagResolver.source(for: loc, skipping: Set(urls)), .fallback)
    }

    func test_skippingNothing_matchesSource() {
        let loc = StubLocation(name: "Buffalo", region: "NY", countryCode: "US")
        XCTAssertEqual(FlagResolver.source(for: loc, skipping: []), FlagResolver.source(for: loc))
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

/// `FlagView` gives a source up for good only when loading it again cannot
/// help, so a launch without network does not leave rows on the country flag
/// or the globe after the connection returns.
final class FlagLoadFailureTests: XCTestCase {
    private func statusError(_ status: Int) -> NSError {
        NSError(
            domain: SDWebImageErrorDomain,
            code: SDWebImageError.Code.invalidDownloadStatusCode.rawValue,
            userInfo: [SDWebImageErrorDownloadStatusCodeKey: status]
        )
    }

    private func sdError(_ code: SDWebImageError.Code) -> NSError {
        NSError(domain: SDWebImageErrorDomain, code: code.rawValue)
    }

    func test_notFound_isMissing() {
        XCTAssertTrue(FlagLoadFailure.isMissingFlag(statusError(404)))
        XCTAssertEqual(FlagLoadFailure.statusCode(of: statusError(404)), 404)
    }

    func test_otherClientErrors_areMissing() {
        XCTAssertTrue(FlagLoadFailure.isMissingFlag(statusError(403)))
        XCTAssertTrue(FlagLoadFailure.isMissingFlag(statusError(410)))
    }

    func test_requestTimeoutAndRateLimit_areNotMissing() {
        XCTAssertFalse(FlagLoadFailure.isMissingFlag(statusError(408)))
        XCTAssertFalse(FlagLoadFailure.isMissingFlag(statusError(429)))
    }

    func test_serverErrors_areNotMissing() {
        XCTAssertFalse(FlagLoadFailure.isMissingFlag(statusError(500)))
        XCTAssertFalse(FlagLoadFailure.isMissingFlag(statusError(503)))
    }

    func test_networkErrors_areNotMissing() {
        let codes = [
            NSURLErrorNotConnectedToInternet,
            NSURLErrorTimedOut,
            NSURLErrorCannotFindHost,
            NSURLErrorCannotConnectToHost,
            NSURLErrorNetworkConnectionLost,
            NSURLErrorCancelled
        ]
        for code in codes {
            let error = NSError(domain: NSURLErrorDomain, code: code)
            XCTAssertFalse(FlagLoadFailure.isMissingFlag(error), "NSURLError \(code)")
            XCTAssertNil(FlagLoadFailure.statusCode(of: error))
        }
    }

    func test_cancelledLoad_isNotMissing() {
        XCTAssertFalse(FlagLoadFailure.isMissingFlag(sdError(.cancelled)))
    }

    func test_undecodableFile_isMissing() {
        XCTAssertTrue(FlagLoadFailure.isMissingFlag(sdError(.badImageData)))
        XCTAssertTrue(FlagLoadFailure.isMissingFlag(sdError(.invalidURL)))
    }

    func test_urlSDWebImageBlocked_isMissing() {
        XCTAssertTrue(FlagLoadFailure.isMissingFlag(sdError(.blackListed)))
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
