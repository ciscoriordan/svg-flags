import Foundation

/// Minimum surface a consumer type needs to expose for `FlagResolver` to do its
/// city → state → country → globe walk. Consumers conform their own location
/// types to this without giving up control of their own model.
public protocol FlagLocatable {
    /// Visible city name in whatever language the consumer is currently
    /// rendering. Falls back to this when `nativeName` is nil.
    var name: String { get }

    /// Visible region/state/province, in the user's language. May be a full
    /// name ("British Columbia"), a 2–3 letter ISO code ("BC"), or nil.
    var region: String? { get }

    /// Visible country name in the user's language. Used only as a fallback
    /// when `countryCode` is missing.
    var country: String? { get }

    /// ISO 3166-1 alpha-2 country code, case insensitive. Strongly preferred
    /// over name-based country resolution.
    var countryCode: String? { get }

    /// Canonical English / Latin city name. Lookups try this first because
    /// `name` may have been swapped to the user's locale (e.g. "Αθήνα").
    /// Default implementation returns `name`.
    var nativeName: String { get }

    /// Canonical English / Latin region name. Default returns `region`.
    var nativeRegion: String? { get }

    /// Canonical English / Latin country name. Default returns `country`.
    var nativeCountry: String? { get }
}

public extension FlagLocatable {
    var nativeName: String { name }
    var nativeRegion: String? { region }
    var nativeCountry: String? { country }
}
