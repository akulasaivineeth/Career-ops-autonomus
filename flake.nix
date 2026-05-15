# Nix dev shell for Career-ops-autonomus (see BUILD.md "Tech Stack").
# Supports Linux CI and macOS; extend with darwin-only packages when needed.
{
  description = "Career-ops-autonomus — autonomous job-application stack (dev shell)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

  outputs =
    { self, nixpkgs }:
    let
      forAllSystems =
        f:
        nixpkgs.lib.genAttrs [
          "aarch64-linux"
          "x86_64-linux"
          "aarch64-darwin"
          "x86_64-darwin"
        ] (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (
        pkgs:
        let
          # Playwright's Chromium often needs these at runtime (Linux); macOS uses system libs.
          playwrightLinuxLibs = pkgs.lib.optionals pkgs.stdenv.isLinux (
            with pkgs;
            [
              nss
              nspr
              atk
              at-spi2-atk
              cups
              dbus
              libdrm
              libxkbcommon
              mesa
              xorg.libXcomposite
              xorg.libXdamage
              xorg.libXext
              xorg.libXfixes
              xorg.libXrandr
              xorg.libxcb
              xorg.libxshmfence
              gtk3
              pango
              cairo
              gdk-pixbuf
              glib
              alsa-lib
            ]
          );
        in
        {
          default = pkgs.mkShell {
            packages =
              with pkgs;
              [
                python312
                uv
                nodejs_20
                go_1_22
                sqlite
                openssl
                pkg-config
              ]
              ++ playwrightLinuxLibs;

            shellHook = ''
              echo "[career-ops] dev shell — python 3.12 + uv + node 20 + go 1.22 (see BUILD.md)"
            '';
          };
        }
      );
    };
}
