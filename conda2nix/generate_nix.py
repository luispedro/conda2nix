TEMPLATE = '''
{{ {dependencies} }}:

stdenv.mkDerivation rec {{
  pname = "{pname}";
  version = "{version}";

  {src}

  buildInputs = [ {buildInputs} ];
  nativeBuildInputs = [ {nativeBuildInputs} ];

  checkPhase = ''

  {checkPhase}

  '';

  buildPhase = ''

  {buildPhase}

  '';

  meta = with stdenv.lib; {{
    description = "{description}";
    homepage = {homepage};
    platforms = platforms.all;
    maintainers = with maintainers; [ luispedro ];
  }};
}}
'''

TEMPLATE_SRC_GH = '''
  src = fetchFromGitHub {{
    repo = "{repo}";
    owner = "{owner}";
    rev = "{rev}";
    sha256 = "{sha256}";
  }};
'''

TEMPLATE_SRC_URL = '''
  src = fetchurl {{
    url = "{url}";
    sha256 = "{sha256}";
  }};
'''

