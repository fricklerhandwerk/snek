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
  shell = pkgs.mkShell {
    packages = [
      snek
      pkgs.npins
    ];
  };
}
