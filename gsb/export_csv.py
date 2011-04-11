# -*- coding: iso-8859-15 -*-
import codecs, csv, cStringIO


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__( self, f, encoding ):
        self.reader = codecs.getreader( encoding )( f )

    def __iter__( self ):
        return self

    def next( self ):
        return self.reader.next().encode( "utf-8" )

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__( self, f, dialect = csv.excel, encoding = "utf-8", **kwds ):
        f = UTF8Recoder( f, encoding )
        self.reader = csv.reader( f, dialect = dialect, **kwds )

    def next( self ):
        row = self.reader.next()
        return [unicode( s, "utf-8" ) for s in row]

    def __iter__( self ):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__( self, f, dialect = csv.excel, encoding = "utf-8", **kwds ):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer( self.queue, dialect = dialect, **kwds )
        self.stream = f
        self.encoder = codecs.getincrementalencoder( encoding )()

    def writerow( self, row ):
        self.writer.writerow( [unicode( s ).encode( "utf-8" ) for s in row] )
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode( "utf-8" )
        # ... and reencode it into the target encoding
        data = self.encoder.encode( data )
        # write to the target stream
        self.stream.write( data )
        # empty queue
        self.queue.truncate( 0 )

    def writerows( self, rows ):
        for row in rows:
            self.writerow( row )

class excel_csv( csv.Dialect ):
    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\r\n'
    quoting = csv.QUOTE_MINIMAL

def export_csv( filename ):
    csv.register_dialect( "excel_csv", excel_csv )
    f = open( filename, "wb" )
    csv = UnicodeWriter( f, encoding = 'iso-8859-15', dialect = excel_csv )
    csv.writerow( u'ID;Account name;date;montant;P;M;moyen;cat;Tiers;Notes;projet;N chq;id lié;op vent M;num op vent M;mois'.split( ';' ) )
    opes = g.ope.get_all_by_date()
    i = 0
    for ope in opes:
        i = i + 1
        ligne = []
        ligne.append( ope['num'] )
        ligne.append( g.compte.get_text( ope['num_compte'] ) )
        ligne.append( ope['date_ope'].strftime( '%d/%m/%Y' ) )
        m = str( ope['montant'] )
        ligne.append( grisbi.int2float( m ) )
        if ope['rappro'] == None:
            ligne.append( 1 )
        else:
            ligne.append( ope['rappro'] )
        ligne.append( ope['pointe'] )
        ligne.append( g.moyen.get_text( ope['num_moyen'], ope['num_compte'] ) )
        ligne.append( '/'.join( ( g.cat.get_text( ope['num_cat'] ), g.scat.get_text( ope['scat'], ope['num_cat'] ) ) ) )
        ligne.append( ope['tiers'] )
        ligne.append( ope['note'] )
        if ope['num_ib'] == - 1:
            ligne.append( '' )
        else:
            ligne.append( ope['num_ib'] )
        ligne.append( ope['numero_cheque'] )
        if ope['num_jumelle'] == - 1:
            ligne.append( 0 )
        else:
            ligne.append( ope['num_jumelle'] )
        ligne.append( ope['ovm'] )
        if ope['num_mere'] == - 1:
            ligne.append( 0 )
        else:
            ligne.append( ope['num_mere'] )
        d = ope['date_ope']
        d = d.strftime( '%Y_%m' )
        ligne.append( d )
        csv.writerow( ligne )
        if ( i // 100.0 ) == ( i / 100.0 ):
            print "ligne %s" % ope['num']
        f.close()

if __name__ == 'main':
    export_csv( 'toto.csv' )
