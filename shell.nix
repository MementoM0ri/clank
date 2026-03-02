{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    python311Packages.pdf2image
    python311Packages.pydantic
    python311Packages.ollama
    python311Packages.pypdf2
    poppler_utils
    ollama
    tkinter
    
  ];

  shellHook = ''
    echo "clank dev shell ready"
    echo "Run 'ollama serve' in a separate terminal if not already running"
    echo "Model required: llama3.2-vision (ollama pull llama3.2-vision)"
  '';
}
