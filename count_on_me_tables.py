import numpy as np, pandas as pd

JOURNALS = ['AER', 'ECA', 'JPE', 'QJE']
TIES   = ['Tconn_pool', 'Tconn_ever', 'Tconn_advisor', 'Tconn_phd', 'Tconn_author', 'key_jel_ref']
LABELS = ['Pooled', 'Same Faculty', 'Ph.D. Advisor', 'Same Ph.D.', 'Co-author', 'Same Field']
OUTS   = [('n', 'Number of articles'), ('page', 'Number of pages'), ('lead', 'Number of lead articles')]

def depvar(o, t):
    return f'{o}_{t}'

def stars(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return ''
    return '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.10 else ''

# ---------------------------------------------------------------- Table 1 of Colussi (2018)
def colussi_table1(final_sample, articles, authors):
    '''Articles' characteristics as in Colussi (2018, Table 1), following TABLE1.do.'''
    d = pd.read_stata(final_sample)
    for x in ['Tconn_phd', 'Tconn_advisor', 'Tconn_ever', 'Tconn_author', 'Tconn_pool', 'refedit']:
        d[x] = d[x].fillna(0)
        d.loc[d.incharge == 0, x] = 0
        d['tie_' + x] = d.groupby('articletitle')[x].transform('max')
    a = d.drop_duplicates('articletitle').copy()
    tag = {'QJE': 'Q J ECON', 'AER': 'AM ECON REV', 'JPE': 'J POLIT ECON', 'ECA': 'ECONOMETRICA'}
    def own_share(r):
        refs = r.references.split(';')[:177] if isinstance(r.references, str) else []
        k = sum(1 for q in refs if tag[r.journal] in q)
        return 100 * k / r.n_references if r.n_references and r.n_references > 0 else 0.0
    a['own_ref'] = a.apply(own_share, axis=1)
    a['pages'] = a.last_page - a.first_page          # as in TABLE1.do (no +1)
    a['single'] = 100 * (a.n_authors == 1)
    jel = []
    for _, r in a.iterrows():
        codes = {r[f'article_jel{i}'][:1] for i in range(1, 8)
                 if isinstance(r[f'article_jel{i}'], str) and r[f'article_jel{i}'] != ''}
        jel += [(r.journal, c) for c in codes]
    jel = pd.DataFrame(jel, columns=['journal', 'JEL'])
    A = pd.read_stata(articles, columns=['journal', 'author', 'year'])
    U = pd.read_stata(authors, columns=['author', 'year', 'faculty_author'])
    m = A.merge(U, on=['author', 'year'], how='inner')
    hhi = {}
    for j in JOURNALS:
        s = m[m.journal == j]
        sh = s.groupby('faculty_author').size() / len(s)
        hhi[j] = (sh ** 2).sum()
    hhi['All'] = np.mean([hhi[j] for j in JOURNALS])   # Colussi's "All" is the mean of the journal indices
    out = {}
    for g in ['All'] + JOURNALS:
        sub = a if g == 'All' else a[a.journal == g]
        js = jel if g == 'All' else jel[jel.journal == g]
        share = js.JEL.value_counts(normalize=True) * 100
        c = {'Articles': len(sub), 'Pages': sub.pages.mean(), 'Citations (8 years)': sub.citation8.mean(),
             'Authors': sub.n_authors.mean(), 'Single author (\\%)': sub.single.mean()}
        for L in ['C', 'D', 'E', 'G', 'I', 'J', 'L', 'O']:
            c['JEL ' + L] = share.get(L, 0.0)
        c['References: number'] = sub.n_references.mean()
        c['References: same journal (\\%)'] = sub.own_ref.mean()
        c['References: editor cited (\\%)'] = 100 * sub.tie_refedit.mean()
        for x, l in [('phd', 'Same Ph.D.'), ('advisor', 'Ph.D. Advisor'), ('ever', 'Same Faculty'),
                     ('author', 'Co-author'), ('pool', 'Pooled')]:
            c['Connected: ' + l] = 100 * sub['tie_Tconn_' + x].mean()
        c['HHI index'] = hhi[g]
        out[g] = c
    return pd.DataFrame(out)

def tex_descriptives(orig, corr):
    rows = list(orig.index)
    groups = [('Articles', ['Articles', 'Pages', 'Citations (8 years)', 'Authors', 'Single author (\\%)']),
              ('References', ['References: number', 'References: same journal (\\%)', 'References: editor cited (\\%)']),
              ('Connected papers (\\%)', [r for r in rows if r.startswith('Connected: ')])]
    def fmt(r, v):
        if r == 'Articles':
            return f'{int(round(v)):,}'
        if r == 'HHI index':
            return f'{v:.3f}'
        return f'{v:.2f}'
    def lab(r):
        for p in ['JEL ', 'References: ', 'Connected: ']:
            if r.startswith(p):
                r = r[len(p):]
                return '\\quad ' + (r[0].upper() + r[1:])
        return r
    h = []
    h.append('\\begin{table}[!htbp]')
    h.append('\\renewcommand{\\arraystretch}{1.25}')
    h.append('\\centering')
    h.append('\\setstretch{1}')
    h.append('\\caption{Articles\' characteristics in the original and corrected data}')
    h.append('\\label{tab:descriptives}')
    h.append('\\small')
    h.append('\\setlength{\\tabcolsep}{2pt}')
    h.append('\\begin{tabular*}{\\linewidth}{@{\\extracolsep{\\fill}}l' + 'cc' * 5 + '}')
    h.append('\\toprule')
    h.append(' & ' + ' & '.join(f'\\multicolumn{{2}}{{c}}{{{g}}}' for g in ['All'] + JOURNALS) + ' \\\\')
    h.append(''.join(f'\\cmidrule(lr){{{2 + 2 * k}-{3 + 2 * k}}}' for k in range(5)))
    h.append(' & ' + ' & '.join(['Orig.', 'Corr.'] * 5) + ' \\\\')
    h.append('\\midrule')
    for title, rs in groups:
        if title and title != 'Articles':
            h.append(f'\\multicolumn{{11}}{{l}}{{\\textit{{{title}}}}} \\\\')
        for r in rs:
            vals = []
            for g in ['All'] + JOURNALS:
                vals += [fmt(r, orig.loc[r, g]), fmt(r, corr.loc[r, g])]
            h.append(lab(r) + ' & ' + ' & '.join(vals) + ' \\\\')
    h.append('\\bottomrule')
    h.append('\\end{tabular*}')
    h.append('\\begin{minipage}{\\linewidth}')
    h.append('\\vspace{4pt}')
    h.append('\\footnotesize\\textit{Notes:} ``Orig.\'\' reproduces \\citeauthor{Colussi2018}\'s '
             '\\citeyearpar[p. 46]{Colussi2018} Table 1 from his replication files; ``Corr.\'\' applies the same code '
             'to the corrected data (eight recovered articles, eight added authors and 19 bibliographic corrections). '
             'Pages are last minus first page. '
             '``Same journal\'\' is the share of an article\'s references published in the same journal; '
             '``Editor cited\'\' is the share of articles flagged as citing an editor in charge by the original code. '
             'An article is connected if at least one author has the tie with an editor in charge at publication. '
             'Sample averages reported for ``Pages,\'\' ``Citations (8 years),\'\' ``authors,\'\' and ``Number.\'\'')
    h.append('\\end{minipage}')
    h.append('\\end{table}')
    return '\n'.join(h)

# ---------------------------------------------------------------- PPML version of Table 3
def tex_ppml_table3(pp):
    """Table 2 of the paper. pp[(o, t)] = dict(b, se, p, N, editors), all from ppmlhdfe."""
    h = []
    h.append('\\begin{table}[!htbp]')
    h.append('\\renewcommand{\\arraystretch}{1.0}')
    h.append('\\centering')
    h.append('\\setstretch{1}')
    h.append('\\caption{Social ties and publication outcomes: Poisson pseudo-maximum-likelihood estimates of '
             '\\citeauthor{Colussi2018}\'s \\citeyearpar[p. 49]{Colussi2018} Table 3 on the corrected data}')
    h.append('\\label{tab:ppml_table3}')
    h.append('\\small')
    h.append('\\setlength{\\tabcolsep}{3pt}')
    h.append('\\begin{tabular}{lcccccc}')
    h.append('\\toprule')
    h.append(' & ' + ' & '.join(LABELS) + ' \\\\')
    h.append(' & ' + ' & '.join(f'({k + 1})' for k in range(6)) + ' \\\\')
    h.append('\\midrule')
    for i, (o, ol) in enumerate(OUTS):
        h.append(f'\\multicolumn{{7}}{{l}}{{\\textit{{{"ABC"[i]}. {ol}}}}} \\\\[2pt]')
        h.append('\\quad PPML coefficient, $\\hat\\beta$ & ' + ' & '.join(f"{pp[(o, t)]['b']:.4f}{stars(pp[(o, t)]['p'])}" for t in TIES) + ' \\\\')
        h.append(' & ' + ' & '.join(f"({pp[(o, t)]['se']:.4f})" for t in TIES) + ' \\\\')
        h.append('\\quad $100[\\exp(\\hat\\beta)-1]$ & ' + ' & '.join(f"{100 * (np.exp(pp[(o, t)]['b']) - 1):.3f}{stars(pp[(o, t)]['p'])}" for t in TIES) + ' \\\\')
        h.append(' & ' + ' & '.join(f"({100 * np.exp(pp[(o, t)]['b']) * pp[(o, t)]['se']:.3f})" for t in TIES) + ' \\\\')
        h.append('\\quad Observations & ' + ' & '.join(f"{int(pp[(o, t)]['N'])}" for t in TIES) + ' \\\\')
        sep = '[8pt]' if i < 2 else ''
        h.append('\\quad Editors & ' + ' & '.join(f"{int(pp[(o, t)]['editors'])}" for t in TIES) + f' \\\\{sep}')
    h.append('\\midrule')
    h.append('Editor $\\times$ Journal FE & ' + ' & '.join(['Yes'] * 6) + ' \\\\')
    h.append('Journal $\\times$ Term FE & ' + ' & '.join(['Yes'] * 6) + ' \\\\')
    h.append('\\bottomrule')
    h.append('\\end{tabular}')
    h.append('\\begin{minipage}{\\linewidth}')
    h.append('\\vspace{4pt}')
    h.append('\\footnotesize\\textit{Notes:} PPML estimates (\\texttt{ppmlhdfe}) on the corrected data, with editor-by-journal '
             'and journal-by-term fixed effects. Both rows come from the same regression: $\\hat\\beta$ is the coefficient on '
             '\\texttt{Incharge} and $100[\\exp(\\hat\\beta)-1]$ the percentage effect, with a delta-method standard error. '
             '``Observations\'\' and ``Editors\'\' give the sample after separated observations are dropped. '
             'Standard errors clustered by journal and half-year term in parentheses. '
             '*** $p<0.01$, ** $p<0.05$, * $p<0.1$.')
    h.append('\\end{minipage}')
    h.append('\\end{table}')
    return '\n'.join(h)

# ---------------------------------------------------------------- comparison table (Table 3 of the paper)
def pct_ols(r, ybar):
    return dict(v=100 * r['b'] / ybar, se=100 * r['se'] / ybar, p=r['p'])

def pct_ppml(r):
    return dict(v=100 * (np.exp(r['b']) - 1), se=100 * np.exp(r['b']) * r['se'], p=r['p'])

def fmt_p(p):
    return '$<$0.001' if p < 0.001 else f'{p:.3f}'

def tex_comparison(ols_o, ols_c, pp, reset, ybar_o, ybar_c, reset_ols):
    h = []
    h.append('\\begin{table}[!htbp]')
    h.append('\\renewcommand{\\arraystretch}{0.95}')
    h.append('\\centering')
    h.append('\\setstretch{1}')
    h.append('\\caption{Effect of an editor being in charge on the output of tied scholars: original estimates, '
             'corrected data with OLS and corrected data with PPML}')
    h.append('\\label{tab:comparison}')
    h.append('\\footnotesize')
    h.append('\\begin{tabular*}{\\linewidth}{@{\\extracolsep{\\fill}}lccccc}')
    h.append('\\toprule')
    h.append(' & Original & \\multicolumn{2}{c}{Corrected data} & \\multicolumn{2}{c}{RESET $p$-value} \\\\')
    h.append('\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}')
    h.append(' & OLS & OLS & PPML & OLS & PPML \\\\')
    h.append(' & (1) & (2) & (3) & (4) & (5) \\\\')
    h.append('\\midrule')
    for i, (o, ol) in enumerate(OUTS):
        h.append(f'\\multicolumn{{6}}{{l}}{{\\textit{{{"ABC"[i]}. {ol}}}}} \\\\[2pt]')
        for t, l in zip(TIES, LABELS):
            c1 = pct_ols(ols_o[(o, t)], ybar_o[(o, t)])
            c2 = pct_ols(ols_c[(o, t)], ybar_c[(o, t)])
            c3 = pct_ppml(pp[(o, t)])
            h.append(f'\\quad {l} & ' + ' & '.join(f"{c['v']:.3f}{stars(c['p'])}" for c in (c1, c2, c3))
                     + f" & {fmt_p(reset_ols[(o, t)])} & {fmt_p(reset[(o, t)])} \\\\")
            h.append(' & ' + ' & '.join(f"({c['se']:.3f})" for c in (c1, c2, c3)) + ' & & \\\\')
        if i < 2:
            h[-1] = h[-1] + '[8pt]'
    h.append('\\bottomrule')
    h.append('\\end{tabular*}')
    h.append('\\begin{minipage}{\\linewidth}')
    h.append('\\vspace{4pt}')
    h.append('\\footnotesize\\textit{Notes:} Percentage effects of an editor being in charge. Columns (1) and (2) divide the '
             'OLS coefficient by the sample mean of the outcome, as in \\citet{Colussi2018}, on his files and on the corrected data. '
             'Column (3) is $100[\\exp(\\hat\\beta)-1]$ from Table \\ref{tab:ppml_table3}. Columns (4) and (5) are RESET $p$-values '
             'for the OLS and PPML models on the corrected data. Standard errors clustered by journal and half-year term '
             'in parentheses. *** $p<0.01$, ** $p<0.05$, * $p<0.1$.')
    h.append('\\end{minipage}')
    h.append('\\end{table}')
    return '\n'.join(h)

# ---------------------------------------------------------------- Appendix B: OLS in levels on the corrected data
def tex_ols_levels(ols_c):
    h = []
    h.append('\\begin{table}[!htbp]')
    h.append('\\renewcommand{\\arraystretch}{1.0}')
    h.append('\\centering')
    h.append('\\setstretch{1}')
    h.append('\\caption{Social ties and publication outcomes on the corrected data: a narrow replication of '
             '\\citeauthor{Colussi2018}\'s \\citeyearpar[p. 49]{Colussi2018} Table 3}')
    h.append('\\label{tab:table3_reghdfe_extended}')
    h.append('\\small')
    h.append('\\setlength{\\tabcolsep}{3pt}')
    h.append('\\begin{tabular}{lcccccc}')
    h.append('\\toprule')
    h.append(' & ' + ' & '.join(LABELS) + ' \\\\')
    h.append(' & ' + ' & '.join(f'({k + 1})' for k in range(6)) + ' \\\\')
    h.append('\\midrule')
    for i, (o, ol) in enumerate(OUTS):
        h.append(f'\\multicolumn{{7}}{{l}}{{\\textit{{{"ABC"[i]}. {ol}}}}} \\\\[2pt]')
        h.append('\\quad Incharge & ' + ' & '.join(f"{ols_c[(o, t)]['b']:.4f}{stars(ols_c[(o, t)]['p'])}" for t in TIES) + ' \\\\')
        sep = '[3pt]' if i < 2 else ''
        h.append(' & ' + ' & '.join(f"({ols_c[(o, t)]['se']:.4f})" for t in TIES) + f' \\\\{sep}')
    h.append('\\midrule')
    h.append('Editor $\\times$ Journal FE & ' + ' & '.join(['Yes'] * 6) + ' \\\\')
    h.append('Journal $\\times$ Term FE & ' + ' & '.join(['Yes'] * 6) + ' \\\\')
    h.append('Observations & ' + ' & '.join(f"{int(ols_c[('n', t)]['N'])}" for t in TIES) + ' \\\\')
    h.append('\\bottomrule')
    h.append('\\end{tabular}')
    h.append('\\begin{minipage}{\\linewidth}')
    h.append('\\vspace{4pt}')
    h.append('\\footnotesize\\textit{Notes:} Each cell is the \\texttt{Incharge} coefficient of a separate OLS regression '
             '(\\texttt{reghdfe}) on the corrected data, with the outcome in its original units: articles (Panel A), '
             'pages (Panel B) or lead articles (Panel C) per editor and term, written by scholars tied to the editor '
             'through the channel in the column header. All specifications absorb editor-by-journal and journal-by-term '
             'fixed effects. Standard errors clustered by journal and half-year term (56 clusters) are in parentheses. '
             '*** $p<0.01$, ** $p<0.05$, * $p<0.1$.')
    h.append('\\end{minipage}')
    h.append('\\end{table}')
    return '\n'.join(h)

# ---------------------------------------------------------------- Appendix A: bibliographic corrections
def article_corrections(articles_orig, articles_upd):
    """Article-level differences between the original and corrected ARTICLES files.
    Returns (new articles, systematic AER renumbering, individual corrections)."""
    k = ['year', 'journal', 'issue', 'first_page', 'last_page']
    A = pd.read_stata(articles_orig).groupby('articletitle')[k].first()
    B = pd.read_stata(articles_upd).groupby('articletitle')[k].first()
    new = B.loc[~B.index.isin(A.index)].sort_values(['journal', 'year', 'first_page'])
    m = A.join(B, rsuffix='_u', how='inner')
    diff = m[(m[k].values != m[[c + '_u' for c in k]].values).any(axis=1)]
    sysaer = ((diff.journal == 'AER') & (diff.issue_u == diff.issue + 1) & (diff.year == diff.year_u)
              & (diff.first_page == diff.first_page_u) & (diff.last_page == diff.last_page_u))
    return new, diff[sysaer], diff[~sysaer].sort_values(['journal', 'year', 'first_page'])

def tex_corrections(ind):
    names = {'issue': 'issue', 'year': 'year', 'first_page': 'first page', 'last_page': 'last page'}
    order = ['issue', 'year', 'first_page', 'last_page']
    rows_a, rows_b = [], []
    for _, r in ind.iterrows():
        f = [c for c in order if r[c] != r[c + '_u']]
        line = (f"{r.journal} & {int(r.year)} & {int(r.first_page)} & {'; '.join(names[c] for c in f)} & "
                f"{'; '.join(str(int(r[c])) for c in f)} & {'; '.join(str(int(r[c + '_u'])) for c in f)} \\\\")
        (rows_a if ('issue' in f or 'year' in f) else rows_b).append(line)
    h = ['\\begin{table}[!htbp]', '\\renewcommand{\\arraystretch}{1.1}', '\\centering', '\\setstretch{1}',
         '\\caption{Corrections Applied to \\texttt{ARTICLES.dta}}', '\\label{tab:corrections}', '\\small',
         '\\begin{tabular}{llrcll}', '\\toprule',
         'Journal & Year & \\multicolumn{1}{c}{First Page} & Field(s) Corrected & Original Value(s) & Corrected Value(s) \\\\',
         '\\midrule', '\\multicolumn{6}{l}{\\textit{Panel A: Issue-number corrections}} \\\\[2pt]']
    h += rows_a
    h[-1] += '[4pt]'
    h += ['\\multicolumn{6}{l}{\\textit{Panel B: Page-number corrections}} \\\\[2pt]'] + rows_b
    h += ['\\bottomrule', '\\end{tabular}', '\\begin{minipage}{\\linewidth}', '\\vspace{4pt}',
          '\\footnotesize\\textit{Notes:} Articles are identified by journal, year, and original first page. '
          'Semicolons separate multiple corrected fields within the same paper. The systematic renumbering of AER '
          'issues 2 to 4 is not listed.', '\\end{minipage}', '\\end{table}']
    return '\n'.join(h)

# ---------------------------------------------------------------- Appendix C: Stata and Python
def tex_python(py):
    """Appendix C. py[(model, o, t)] = dict(b, se) from fasthdfe; model in ols_orig, ols_corr, ppml."""
    blocks = [('ols_orig', 'OLS, original data'), ('ols_corr', 'OLS, corrected data'), ('ppml', 'PPML, corrected data')]
    h = ['\\begin{table}[!htbp]', '\\renewcommand{\\arraystretch}{0.95}', '\\centering', '\\setstretch{1}',
         '\\caption{Colussi\'s Table 3 estimated in Python}', '\\label{tab:python}', '\\footnotesize',
         '\\begin{tabular*}{\\linewidth}{@{\\extracolsep{\\fill}}l' + 'cc' * 3 + '}', '\\toprule',
         ' & ' + ' & '.join(f'\\multicolumn{{2}}{{c}}{{{bl}}}' for _, bl in blocks) + ' \\\\',
         '\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}',
         ' & ' + ' & '.join(['$\\widehat{\\beta}^\\ast$', 's.e.'] * 3) + ' \\\\', '\\midrule']
    for i, (o, ol) in enumerate(OUTS):
        h.append(f'\\multicolumn{{7}}{{l}}{{\\textit{{{"ABC"[i]}. {ol}}}}} \\\\[2pt]')
        for t, l in zip(TIES, LABELS):
            h.append(f'\\quad {l} & ' + ' & '.join(f"{py[(m, o, t)]['b']:.4f}{stars(py[(m, o, t)]['p'])} & ({py[(m, o, t)]['se']:.4f})" for m, _ in blocks) + ' \\\\')
        if i < 2:
            h[-1] += '[3pt]'
    h += ['\\bottomrule', '\\end{tabular*}', '\\begin{minipage}{\\linewidth}', '\\vspace{4pt}',
          '\\footnotesize\\textit{Notes:} Estimates from the Python package \\texttt{fasthdfe}, with the same fixed effects, '
          'clustering and estimation samples as the Stata commands \\texttt{reghdfe} and \\texttt{ppmlhdfe}. The estimated coefficients '
          '($\\widehat{\\beta}^\\ast$) equal the Stata ones in every cell (\\citeauthor{Colussi2018}\'s Table 3, Table \\ref{tab:table3_reghdfe_extended} '
          'and Table \\ref{tab:ppml_table3}). The standard errors differ only by the small-sample factor '
          '$\\sqrt{(N-1)/(N-K)}$, where $K$ counts \\texttt{Incharge} and the editor-by-journal effects: for OLS, '
          '\\texttt{reghdfe} applies it and \\texttt{fasthdfe} does not; for PPML, \\texttt{fasthdfe} applies it and '
          '\\texttt{ppmlhdfe} does not. Clustered standard errors (s.e.) in parentheses. Stars use the $p$-values reported by \\texttt{fasthdfe}: *** $p<0.01$, ** $p<0.05$, * $p<0.1$.',
          '\\end{minipage}', '\\end{table}']
    return '\n'.join(h)

# ---------------------------------------------------------------- Figure: zeros in the outcomes
def fig_zeros(toreg, path):
    '''Distribution of tied articles and tied lead articles per editor-term cell, by tie.'''
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 9, 'font.family': 'serif', 'axes.titlesize': 9,
                         'axes.labelsize': 9, 'xtick.labelsize': 8, 'ytick.labelsize': 8})
    BLUE, GRAY, INK = '#000000', '#bfbfbf', '#000000'
    rows = [('n', 'Articles', 6), ('lead', 'Lead articles', 3)]
    fig, axes = plt.subplots(2, 6, figsize=(6.5, 3.4), sharey=True)
    for i, (o, olab, top) in enumerate(rows):
        for j, (t, tlab) in enumerate(zip(TIES, LABELS)):
            ax = axes[i, j]
            y = toreg[depvar(o, t)].clip(upper=top)
            share = y.value_counts(normalize=True).reindex(range(top + 1), fill_value=0) * 100
            ax.bar(share.index, share.values, width=0.8, color=[BLUE] + [GRAY] * top, linewidth=0)
            ax.text(0, share[0] + 3, f'{share[0]:.0f}%', ha='center', va='bottom', fontsize=8, color='#0b0b0b')
            ticks = [0, 2, 4, top] if o == 'n' else list(range(top + 1))
            ax.set_xticks(ticks)
            ax.set_xticklabels([f'{k}+' if (o == 'n' and k == top) else str(k) for k in ticks])
            ax.set_ylim(0, 110)
            ax.set_yticks([0, 50, 100])
            ax.set_yticklabels(['0%', '50%', '100%'])
            for s in ('top', 'right'):
                ax.spines[s].set_visible(False)
            for s in ('left', 'bottom'):
                ax.spines[s].set_color(INK)
            ax.tick_params(colors=INK, length=2)
            if i == 0:
                ax.set_title(tlab)
            if j == 0:
                ax.set_ylabel(olab)
    fig.supxlabel('Tied output of the editor in the journal and half-year term', fontsize=9)
    fig.tight_layout(h_pad=1.0, w_pad=0.6)
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)

def fig_zeros_tikz(toreg, path):
    '''pgfplots version of Figure 1: zeros in black, other counts in gray, % on the y axis.'''
    rows = [('n', 'Articles', 6), ('lead', 'Lead articles', 3)]
    h = ['% Figure 1: distribution of tied output across editor-by-term cells (generated by tables_colussi_ppml.ipynb)',
         '\\begin{tikzpicture}',
         '\\begin{groupplot}[',
         '  group style={group size=6 by 2, horizontal sep=0.35cm, vertical sep=1.0cm, y descriptions at=edge left},',
         '  scale only axis, width=2.27cm, height=2.1cm,',
         '  ybar, /pgf/bar shift=0pt, /pgf/bar width=0.24cm, ymin=0, ymax=118, ytick={0,50,100}, yticklabel={\\pgfmathprintnumber{\\tick}\\%},',
         '  axis x line*=bottom, axis y line*=left, tick align=outside, tick style={black, thin}, major tick length=2pt,',
         '  every axis/.append style={font=\\fontsize{9}{10}\\selectfont},',
         '  title style={yshift=-3pt},',
         '  nodes near coords style={font=\\fontsize{8}{9}\\selectfont, anchor=south, xshift=4pt},',
         ']']
    for i, (o, olab, top) in enumerate(rows):
        ticks = [0, 2, 4, top] if o == 'n' else list(range(top + 1))
        tlabels = [f'{k}+' if (o == 'n' and k == top) else str(k) for k in ticks]
        for j, (t, tlab) in enumerate(zip(TIES, LABELS)):
            y = toreg[depvar(o, t)].clip(upper=top)
            share = y.value_counts(normalize=True).reindex(range(top + 1), fill_value=0) * 100
            opts = [f'xmin=0, xmax={top}', 'enlarge x limits={abs=%s}' % ('1.5' if o == 'n' else '0.7'), '/pgf/bar width=%s' % ('0.17cm' if o == 'n' else '0.24cm'), f'xtick={{{",".join(map(str, ticks))}}}',
                    f'xticklabels={{{",".join(tlabels)}}}']
            if i == 0:
                opts.append(f'title={{{tlab}}}')
            if j == 0:
                opts.append(f'ylabel={{{olab}}}')
            h.append('\\nextgroupplot[' + ', '.join(opts) + ']')
            h.append(f'\\addplot[fill=black, draw=none, nodes near coords, '
                     f'point meta=explicit symbolic] coordinates {{(0,{share[0]:.2f}) [{share[0]:.0f}\\%]}};')
            rest = ' '.join(f'({k},{share[k]:.2f})' for k in range(1, top + 1))
            h.append(f'\\addplot[fill=black!25, draw=none] coordinates {{{rest}}};')
    h += ['\\end{groupplot}',
          '\\node[anchor=north, font=\\fontsize{9}{10}\\selectfont] at ($(group c1r2.south west)!0.5!(group c6r2.south east) + (0,-0.6cm)$)',
          '  {Tied output of the editor in the journal and half-year term};',
          '\\end{tikzpicture}']
    path.write_text('\n'.join(h) + '\n', encoding='utf-8')

# ---------------------------------------------------------------- HTML preview of the LaTeX tables
_CITES = {'Colussi2018': ('Colussi', '2018'), 'Ramsey1969': ('Ramsey', '1969'), 'fasthdfe': ('Larch', '2026'),
          'Correia_ppmlhdfe': ('Correia, Guimarães and Zylkin', '2020'), 'SST2006': ('Santos Silva and Tenreyro', '2006'),
          'SSW2026': ('Santos Silva and Winkelmann', '2026')}

def _tex_inline(x):
    '''Turn the small subset of LaTeX used in our tables into HTML.'''
    import re
    x = x.strip()
    cite = lambda k: _CITES.get(k, (k, ''))
    x = re.sub(r"\\citeauthor\{(\w+)\}'s \\citeyearpar\[([^\]]*)\]\{(\w+)\}",
               lambda m: f"{cite(m.group(1))[0]}'s ({cite(m.group(1))[1]}, {m.group(2)})", x)
    x = re.sub(r'\\citeauthor\{(\w+)\}', lambda m: cite(m.group(1))[0], x)
    x = re.sub(r'\\citeyearpar\{(\w+)\}', lambda m: f'({cite(m.group(1))[1]})', x)
    x = re.sub(r'\\citet\{(\w+)\}', lambda m: f'{cite(m.group(1))[0]} ({cite(m.group(1))[1]})', x)
    x = re.sub(r'\\citep\{([\w, ]+)\}', lambda m: '(' + '; '.join(', '.join(cite(k.strip())) for k in m.group(1).split(',')) + ')', x)
    x = re.sub(r'Table[~ ]\\ref\{tab:(\w+)\}', lambda m: {'ppml_table3': 'Table 2', 'comparison': 'Table 3',
               'table3_reghdfe_extended': 'Table B-1', 'descriptives': 'Table 1', 'python': 'Table C-1',
               'corrections': 'Table A-3'}.get(m.group(1), 'Table'), x)
    rep = [('$<$', '&lt;'), ('\\widehat{\\beta}^\\ast', 'β̂*'), ('\\hat\\beta', 'β̂'), ('\\beta', 'β'), ('\\exp', 'exp'), ('\\times', '×'),
           ('\\mathrm{se}', 'se'), ('\\mid', '|'), ('\\,', ' '), ('\\%', '%'), ('~', ' '), ('``', '“'), ("''", '”'),
           ('\\quad ', '&emsp;'), ('\\ ', ' '), ('_{ijt}', '<sub>ijt</sub>'), ("x_{ijt}'", "x<sub>ijt</sub>′")]
    for a, b in rep:
        x = x.replace(a, b)
    x = re.sub(r'\\textit\{([^{}]*)\}', r'<i>\1</i>', x)
    x = re.sub(r'\\emph\{([^{}]*)\}', r'<i>\1</i>', x)
    x = re.sub(r'\\texttt\{([^{}]*)\}', r'<code>\1</code>', x)
    x = re.sub(r'\\sqrt\{([^{}]*)\}', r'√(\1)', x)
    x = x.replace('$', '').replace('<p', '&lt;p') if False else x.replace('$', '')
    x = re.sub(r'\\\w+\{([^{}]*)\}', r'\1', x)
    return x.replace('{', '').replace('}', '')

def tex_to_html(tex):
    '''HTML version of a table written by this module: same caption, rows, panels and notes.'''
    import re
    cap = re.search(r'\\caption\{(.*?)\}\n\\label', tex, re.S).group(1)
    body = tex[tex.index('\\toprule'):tex.index('\\bottomrule')]
    note = re.search(r'\\textit\{Notes:\}(.*?)\n?\\end\{minipage\}', tex, re.S)
    ncol = len(re.search(r'\\begin\{tabular\*?\}(?:\{\\linewidth\})?\{(?:@\{\\extracolsep\{\\fill\}\})?([lcr]+)\}', tex).group(1))
    css = ('border-collapse:collapse;font-family:serif;font-size:13px;margin:6px 0;')
    lab = re.search(r'\\label\{tab:(\w+)\}', tex).group(1)
    num = {'descriptives': 'Table 1', 'ppml_table3': 'Table 2', 'comparison': 'Table 3', 'corrections': 'Table A-3',
           'table3_reghdfe_extended': 'Table B-1', 'python': 'Table C-1'}.get(lab, 'Table')
    out = ['<div style="margin:10px 0">', f'<table style="{css}">',
           f'<tr><td colspan="{ncol}" style="text-align:left;white-space:normal;font-size:14px;padding:4px 0"><div style="width:0;min-width:100%">{num}: {_tex_inline(cap)}</div></td></tr>']
    top = 'border-top:2px solid black;'
    pending = top
    for line in body.split('\n'):
        line = line.strip()
        if not line or line.startswith('\\toprule') or line.startswith('\\cmidrule'):
            continue
        if line.startswith('\\midrule'):
            pending = 'border-top:1px solid black;'
            continue
        gap = re.search(r'\\\\\[(\d+)pt\]$', line)
        line = re.sub(r'\\\\(\[\d+pt\])?$', '', line)
        cells = [c for c in re.split(r'(?<!\\)&', line)]
        tds = []
        for k, c in enumerate(cells):
            c = c.strip()
            m = re.match(r'\\multicolumn\{(\d+)\}\{([lcr])\}\{(.*)\}$', c)
            span, align, txt = (int(m.group(1)), m.group(2), m.group(3)) if m else (1, 'l' if k == 0 else 'c', c)
            al = {'l': 'left', 'c': 'center', 'r': 'right'}[align]
            tds.append(f'<td colspan="{span}" style="text-align:{al};padding:1px 8px;white-space:nowrap;{pending}">{_tex_inline(txt)}</td>')
        row = '<tr>' + ''.join(tds) + '</tr>'
        if gap:
            row += f'<tr><td colspan="{ncol}" style="height:{int(gap.group(1)) + 2}px;padding:0"></td></tr>'
        out.append(row)
        pending = ''
    out.append(f'<tr><td colspan="{ncol}" style="border-top:2px solid black;padding:0"></td></tr>')
    if note:
        out.append(f'<tr><td colspan="{ncol}" style="text-align:left;white-space:normal;font-size:12px;padding:4px 0">'
                   f'<div style="width:0;min-width:100%"><i>Notes:</i> {_tex_inline(note.group(1))}</div></td></tr>')
    out.append('</table></div>')
    return '\n'.join(out)
