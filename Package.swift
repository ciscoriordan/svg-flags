// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "SVGFlags",
    platforms: [
        .iOS(.v17),
        .macOS(.v13)
    ],
    products: [
        .library(
            name: "SVGFlags",
            targets: ["SVGFlags"]
        )
    ],
    dependencies: [
        .package(url: "https://github.com/SDWebImage/SDWebImage.git", from: "5.19.0"),
        .package(url: "https://github.com/SDWebImage/SDWebImageSwiftUI.git", from: "3.1.0"),
        .package(url: "https://github.com/SDWebImage/SDWebImageSVGCoder.git", from: "1.7.0")
    ],
    targets: [
        .target(
            name: "SVGFlags",
            dependencies: [
                .product(name: "SDWebImage", package: "SDWebImage"),
                .product(name: "SDWebImageSwiftUI", package: "SDWebImageSwiftUI"),
                .product(name: "SDWebImageSVGCoder", package: "SDWebImageSVGCoder")
            ],
            resources: [
                .process("Resources/Flags.xcassets"),
                .process("Resources/cityFlagMap.json"),
                .process("Resources/subdivisionMap.json")
            ]
        ),
        .testTarget(
            name: "SVGFlagsTests",
            dependencies: ["SVGFlags"]
        )
    ]
)
