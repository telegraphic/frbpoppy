"""Determine whether frbpoppy can explain CHIME results."""
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
import numpy as np
from scipy.stats import ks_2samp

from frbcat import ChimeRepeaters
from frbpoppy import Frbcat, split_pop, unpickle, hist

from tests.convenience import plot_aa_style, rel_path

N_DAYS = 100


def get_frbcat_data():
    """Get all chime data from frbcat.

    Returns:
        dict: Two keys 'r' for repeater and 'o' for one-offs. Each
            with entries for 'dm' and 'snr'

    """
    fc = Frbcat(frbpoppy=False, repeaters=True)
    chime_df = fc.df[fc.df.telescope == 'chime']
    chime_df = chime_df.sort_values(by=['frb_name'])

    frbcat = {'r': {}, 'o': {}}

    # Chime one-offs
    chime_o = chime_df.drop_duplicates(subset=['frb_name'], keep=False)

    # Chime repeaters
    chime_r = chime_df.loc[chime_df['frb_name'].duplicated(), :]
    # Actually use the Chime repeaters database
    chime_r = ChimeRepeaters().df.sort_values(by='name')

    # One DM value per repeater (used the average between bursts)
    frbcat['r']['dm'] = chime_r.groupby('name').mean().reset_index().dm
    frbcat['o']['dm'] = chime_o.dm

    # All the different SNRs per repeater (or one_offs)
    frbcat['r']['snr'] = chime_r.sort_values('timestamp').groupby('name').snr.first().values
    frbcat['o']['snr'] = chime_o.snr

    # Number of repeaters vs one offs
    frbcat['r']['n'] = len(frbcat['r']['dm'])
    frbcat['o']['n'] = len(frbcat['o']['dm'])

    return frbcat


def get_frbpoppy_data():
    """Get frbpoppy data."""
    surv_pop = unpickle('cosmic_chime')

    # Split population into seamingly one-off and repeater populations
    mask = ((~np.isnan(surv_pop.frbs.time)).sum(1) > 1)
    pop_ngt1, pop_nle1 = split_pop(surv_pop, mask)
    pop_ngt1.name += ' (> 1 burst)'
    pop_nle1.name += ' (1 burst)'

    frbpop = {'r': {}, 'o': {}}
    for i, pop in enumerate((pop_ngt1, pop_nle1)):
        t = 'o'
        if i == 0:
            t = 'r'
        frbpop[t]['dm'] = pop.frbs.dm
        # Take only the first snr
        frbpop[t]['snr'] = pop.frbs.snr[:, 0]

    return frbpop


def plot(frbcat, frbpop):
    """Plot distributions."""
    # Change working directory
    plot_aa_style(cols=2)

    f, axes = plt.subplots(2, 2, sharex='col', sharey='row')

    axes[1, 0].set_xlabel(r'DM ($\textrm{pc}\ \textrm{cm}^{-3}$)')
    axes[1, 1].set_xlabel(r'S/N')
    axes[1, 1].set_xscale('log')

    axes[1, 0].set_ylabel('Fraction')
    axes[1, 0].set_yscale('log')
    axes[1, 0].set_ylim(3e-2, 1.2e0)
    axes[0, 0].set_ylabel('Fraction')
    axes[0, 0].set_yscale('log')
    axes[0, 0].set_ylim(3e-2, 1.2e0)

    # Set colours
    cmap = plt.get_cmap('tab10')([0, 1])

    # Plot dm distribution
    for i, p in enumerate((frbcat, frbpop)):
        for t in ['r', 'o']:

            # Line style
            linestyle = 'solid'
            label = 'one-offs'
            alpha = 1
            a = 0
            if t == 'r':
                linestyle = 'dashed'
                label = 'repeaters'
                a = 1

            n_bins = 40
            if len(p[t]['dm']) < 20:
                n_bins = 10

            bins = np.linspace(0, 2000, n_bins)
            axes[a, 0].step(*hist(p[t]['dm'], norm='max', bins=bins),
                            where='mid', linestyle=linestyle, label=label,
                            color=cmap[i], alpha=alpha)

            # Plot SNR distribution
            bins = np.logspace(0.5, 3.5, n_bins)
            axes[a, 1].step(*hist(p[t]['snr'], norm='max', bins=bins),
                            where='mid', linestyle=linestyle, label=label,
                            color=cmap[i], alpha=alpha)

    for t in ['r', 'o']:
        for p in ('dm', 'snr'):
            row = 0
            col = 0
            if p == 'snr':
                col = 1
            if t == 'o':
                row = 1

            ks = ks_2samp(frbpop[t][p], frbcat[t][p])
            print(f'KS test: {ks}')

            text = fr'$p={round(ks[1], 2)}$'
            if ks[1] < 0.01:
                text = fr'$p < 0.01$'
            anchored_text = AnchoredText(text, loc='upper right',
                                         borderpad=0.5, frameon=False)
            axes[row, col].add_artist(anchored_text)

    # Set up layout options
    f.subplots_adjust(hspace=0)
    f.subplots_adjust(wspace=0.07)

    # Add legend elements
    elements = []

    def patch(color):
        return Patch(facecolor=color, edgecolor=color)

    elements.append((patch(cmap[0]), 'Frbcat'))
    elements.append((patch(cmap[1]), 'Frbpoppy'))
    # # Add gap in legend
    # elements.append((Line2D([0], [0], color='white'), ''))
    # Add line styles
    elements.append((Line2D([0], [0], color='gray'), 'One-offs'))
    elements.append((Line2D([0], [0], color='gray', linestyle='dashed'),
                     'Repeaters'))

    lines, labels = zip(*elements)

    lgd = plt.figlegend(lines, labels, loc='upper center', ncol=4,
                        framealpha=1,  bbox_to_anchor=(0.485, 1.04),
                        columnspacing=1.1, handletextpad=0.3)
    # plt.tight_layout()
    # plt.legend(lines, labels, bbox_to_anchor=(0.5, 1.04), loc="upper center")

    path = rel_path(f'./plots/frbcat_chime.pdf')
    plt.savefig(path, bbox_extra_artists=(lgd,), bbox_inches='tight')


def main():
    """Run code."""
    frbcat = get_frbcat_data()
    frbpop = get_frbpoppy_data()
    plot(frbcat, frbpop)


if __name__ == '__main__':
    main()
