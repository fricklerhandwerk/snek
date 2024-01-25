{ sources ? import ./npins
, system ? builtins.currentSystem
,
}:
let
  pkgs = import sources.nixpkgs {
    inherit system;
    config = { };
    overlays = [ ];
  };
in
rec {
  snek = with pkgs.python3Packages; buildPythonApplication {
    name = "snek";
    src = ./.;
    buildInputs = [ ];
    propagatedBuildInputs = [ blessed ];
  };
  test-loop = with pkgs; writeShellApplication {
    name = "test-loop";
    text = with pkgs; ''
      ${watchexec}/bin/watchexec --restart --workdir ${toString ./.} python -m snek.main
    '';
  };
  shell = pkgs.mkShell {
    packages = [
      snek
      test-loop
      pkgs.npins
    ];
  };
}
