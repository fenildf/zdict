string DslDictionary::nodeToHtml( ArticleDom::Node const & node )
{
  if ( !node.isTag )
    return Html::escape( Utf8::encode( node.text ) );

  string result;

  if ( node.tagName == GD_NATIVE_TO_WS( L"b" ) )
    result += "<b class=\"dsl_b\">" + processNodeChildren( node ) + "</b>";
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"i" ) )
    result += "<i class=\"dsl_i\">" + processNodeChildren( node ) + "</i>";
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"u" ) )
  {
    string nodeText = processNodeChildren( node );

    if ( nodeText.size() && isDslWs( nodeText[ 0 ] ) )
      result.push_back( ' ' ); // Fix a common problem where in "foo[i] bar[/i]"
                               // the space before "bar" gets underlined.

    result += "<span class=\"dsl_u\">" + nodeText + "</span>";
  }
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"c" ) )
  {
    result += "<font color=\"" + ( node.tagAttrs.size() ?
      Html::escape( Utf8::encode( node.tagAttrs ) ) : string( "c_default_color" ) )
      + "\">" + processNodeChildren( node ) + "</font>";
  }
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"*" ) )
    result += "<span class=\"dsl_opt\">" + processNodeChildren( node ) + "</span>";
  else
  if ( node.tagName.size() == 2 && node.tagName[ 0 ] == L'm' &&
       iswdigit( node.tagName[ 1 ] ) )
    result += "<div class=\"dsl_" + Utf8::encode( node.tagName ) + "\">" + processNodeChildren( node ) + "</div>";
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"trn" ) )
    result += "<span class=\"dsl_trn\">" + processNodeChildren( node ) + "</span>";
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"ex" ) )
    result += "<span class=\"dsl_ex\">" + processNodeChildren( node ) + "</span>";
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"com" ) )
    result += "<span class=\"dsl_com\">" + processNodeChildren( node ) + "</span>";
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"s" ) )
  {
    string filename = Utf8::encode( node.renderAsText() );

    if ( Filetype::isNameOfSound( filename ) )
    {
      // If we have the file here, do the exact reference to this dictionary.
      // Otherwise, make a global 'search' one.

      string n =
        FsEncoding::dirname( getDictionaryFilenames()[ 0 ] ) +
        FsEncoding::separator() +
        FsEncoding::encode( filename );

      bool search =

        !File::exists( n ) && !File::exists( getDictionaryFilenames()[ 0 ] + ".files" +
                                             FsEncoding::separator() +
                                             FsEncoding::encode( filename ) ) &&
          ( !resourceZip.isOpen() ||
            !resourceZip.hasFile( Utf8::decode( filename ) ) );

      QUrl url;
      url.setScheme( "gdau" );
      url.setHost( QString::fromUtf8( search ? "search" : getId().c_str() ) );
      url.setPath( QString::fromUtf8( filename.c_str() ) );

      string ref = string( "\"" ) + url.toEncoded().data() + "\"";

      result += addAudioLink( ref, getId() );

      result += "<span class=\"dsl_s_wav\"><a href=" + ref
         + "><img src=\"qrcx://localhost/icons/playsound.png\" border=\"0\" align=\"absmiddle\" alt=\"Play\"/></a></span>";
    }
    else
    if ( Filetype::isNameOfPicture( filename ) )
    {
      QUrl url;
      url.setScheme( "bres" );
      url.setHost( QString::fromUtf8( getId().c_str() ) );
      url.setPath( QString::fromUtf8( filename.c_str() ) );

      result += string( "<img src=\"" ) + url.toEncoded().data()
             + "\" alt=\"" + Html::escape( filename ) + "\"/>";
    }
    else
    {
      // Unknown file type, downgrade to a hyperlink

      QUrl url;
      url.setScheme( "bres" );
      url.setHost( QString::fromUtf8( getId().c_str() ) );
      url.setPath( QString::fromUtf8( filename.c_str() ) );

      result += string( "<a class=\"dsl_s\" href=\"" ) + url.toEncoded().data()
             + "\">" + processNodeChildren( node ) + "</a>";
    }
  }
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"url" ) )
    result += "<a class=\"dsl_url\" href=\"" + Html::escape( Utf8::encode( node.renderAsText() ) ) +"\">" + processNodeChildren( node ) + "</a>";
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"!trs" ) )
    result += "<span class=\"dsl_trs\">" + processNodeChildren( node ) + "</span>";
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"p") )
  {
    result += "<span class=\"dsl_p\"";

    string val = Utf8::encode( node.renderAsText() );

    // If we have such a key, display a title

    map< string, string >::const_iterator i = abrv.find( val );

    if ( i != abrv.end() )
    {
      string title;

      if ( Utf8::decode( i->second ).size() < 70 )
      {
        // Replace all spaces with non-breakable ones, since that's how
        // Lingvo shows tooltips
        title.reserve( i->second.size() );

        for( char const * c = i->second.c_str(); *c; ++c )
          if ( *c == ' ' || *c == '\t' )
          {
            // u00A0 in utf8
            title.push_back( 0xC2 );
            title.push_back( 0xA0 );
          }
          else
            title.push_back( *c );
      }
      else
        title = i->second;

      result += " title=\"" + Html::escape( title ) + "\"";
    }

    result += ">" + processNodeChildren( node ) + "</span>";
  }
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"'" ) )
  {
    result += "<span class=\"dsl_stress\">" + processNodeChildren( node ) + Utf8::encode( wstring( 1, 0x301 ) ) + "</span>";
  }
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"lang" ) )
  {
    result += "<span class=\"dsl_lang\">" + processNodeChildren( node ) + "</span>";
  }
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"ref" ) )
  {
    QUrl url;

    url.setScheme( "gdlookup" );
    url.setHost( "localhost" );
    url.setPath( gd::toQString( node.renderAsText() ) );

    result += string( "<a class=\"dsl_ref\" href=\"" ) + url.toEncoded().data() +"\">" + processNodeChildren( node ) + "</a>";
  }
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"sub" ) )
  {
    result += "<sub>" + processNodeChildren( node ) + "</sub>";
  }
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"sup" ) )
  {
    result += "<sup>" + processNodeChildren( node ) + "</sup>";
  }
  else
  if ( node.tagName == GD_NATIVE_TO_WS( L"t" ) )
  {
    result += "<span class=\"dsl_t\">" + processNodeChildren( node ) + "</span>";
  }
  else
    result += "<span class=\"dsl_unknown\">" + processNodeChildren( node ) + "</span>";

  return result;
}
