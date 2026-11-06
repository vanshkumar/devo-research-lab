"""Post-freeze presentation adjustment only; no data/model/interval changes.

The frozen renderer placed the scalar-margin legend over the final error bar.
Move that legend into the empty space between rows, using the same frozen
renderer and its saved numerical inputs. Run after reproduce.py if desired.
"""
import figures_tables as frozen
original_save=frozen.save

def save(fig,name):
 if name=='primary_effect':
  ax=fig.axes[1]
  ax.legend(loc='center left',frameon=False,fontsize=8)
 original_save(fig,name)

frozen.save=save
if __name__=='__main__':frozen.main()
