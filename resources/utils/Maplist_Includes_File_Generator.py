# include file header
includes_header = """<includes>
"""
# include file footer
includes_footer = """</includes>
"""
# content header
content_header = """    <include name="MapsList%d.Content">
        <content>
"""
# content footer
content_footer = """        </content>
    </include>

"""
# main content item
item = """            <item>
                <label>$INFO[Window.Property(MapList.%d.MapLabel.%d)]</label>
                <label2>$INFO[Window.Property(MapList.%d.MapLabel2.%d)]</label2>
                <icon>$INFO[Window.Property(MapList.%d.MapIcon.%d)]</icon>
                <onclick>SetProperty(Weather.CurrentMap,$INFO[Window.Property(MapList.%d.MapLabel.%d)])</onclick>
                <onclick>$INFO[Window.Property(MapList.%d.MapOnclick.%d)]</onclick>
                <onclick>SetFocus(2000)</onclick>
                <visible>!IsEmpty(Window.Property(MapList.%d.MapLabel.%d))</visible>
            </item>
"""

map_lists = 3
items = 30
filename = "Maps-List-Static-Content-Includes.xml"
# create file
text = includes_header
for list_count in range( 1, map_lists + 1 ):
    text += content_header % ( list_count, )
    for item_count in range( 1, items + 1 ):
        text += item % ( ( list_count, item_count, ) * 6 )
    text += content_footer
text += includes_footer

# save file
open( filename, "w" ).write( text )
print "created file"
