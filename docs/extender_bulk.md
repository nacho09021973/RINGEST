# Expanded bulk geometry catalog for the RINGEST holographic pipeline

The existing six-family RINGEST catalog can be extended by at least **18 additional well-motivated geometry families** drawn from the holographic, AdS-CMT, and gauge-gravity duality literature. These families span finite-density matter, modified gravity, confinement physics, momentum relaxation, and topological sectors — each producing qualitatively distinct boundary observables. Below is a rigorous, reference-grounded catalog organized by physical regime, with explicit metric data in or convertible to domain wall gauge.

---

## Charged and finite-density geometries open the largest new sector

These families introduce a U(1) chemical potential or charge density, enabling holographic descriptions of compressible quantum matter. They are the single most impactful additions to the catalog because finite density is essential for condensed-matter and QCD applications.

### Family 7: Reissner-Nordström-AdS (RN-AdS)

**Standard notation:** Planar RN-AdS black brane (Einstein-Maxwell theory).

**Metric in Schwarzschild-like coordinates:**
$$ds^2 = -\frac{r^2}{L^2}h(r)\,dt^2 + \frac{L^2\,dr^2}{r^2 h(r)} + \frac{r^2}{L^2}dx_i^2$$

$$h(r) = 1 - (1+Q^2)\!\left(\frac{r_h}{r}\right)^d + Q^2\!\left(\frac{r_h}{r}\right)^{2(d-1)}$$

**Domain wall gauge:** With $u = r_h/r$ and $dz = \frac{Lu\,du}{r_h\sqrt{h(u)}\,u^2}$, one obtains $e^{2A} = r_h^2/(L^2 u^2)$ and $f = h(u(z))$. Near boundary: $A(z)\to -\ln(z/L)$, $f(z)\to 1$. The full $z(u)$ mapping involves an incomplete Beta integral — non-elementary but straightforward numerically.

**Key parameters:** Dimensionless charge $Q$, chemical potential $\mu$, Hawking temperature $T = \frac{r_h}{4\pi L^2}[d - (d-2)Q^2]$. **Extremal limit** $Q^2 = d/(d-2)$ gives $T=0$ with a finite-area horizon.

**Boundary physics:** Finite charge density and chemical potential in a $d$-dimensional CFT. The extremal near-horizon geometry is **AdS$_2\times\mathbb{R}^d$**, producing semi-local quantum criticality and non-Fermi liquid behavior. Probe fermion spectral functions show marginal Fermi liquids (Liu, McGreevy, Vegh, arXiv:0903.2477). Also the parent phase for holographic superconductor instabilities.

**IR behavior:** Non-extremal — regular Rindler horizon, $f\sim 4\pi T(z_h - z)$. Extremal — double zero of $f$ at $z_h$, emergent SL(2,$\mathbb{R}$) symmetry, AdS$_2$ throat with radius $L_2 = L/\sqrt{d(d-1)}$. **Finite ground-state entropy density** $s(T=0)\neq 0$ — a key qualitative distinction from all existing families.

**Distinctness:** YES. Reduces to `ads` family when $Q\to 0$ but has qualitatively different thermodynamics (extremal limit, phase diagram, $T=0$ entropy).

**References:** Chamblin, Emparan, Horowitz, Myers (1999) hep-th/9904197; Hartnoll (2009) arXiv:0903.3246.

---

### Family 8: Gubser-Rocha model (strange metal, $T$-linear resistivity)

**Standard notation:** Gubser-Rocha (GR) EMD model — a specific Einstein-Maxwell-Dilaton theory with analytic black brane solutions.

**Action (5D):** $S = \int d^5x\sqrt{-g}\left[R - \tfrac{1}{2}(\partial\phi)^2 + V(\phi) - \tfrac{1}{4}Z(\phi)F^2\right]$ with $V(\phi) = \frac{12}{L^2}\cosh(\phi/\sqrt{6})$, $Z(\phi) = e^{-2\phi/\sqrt{6}}$. The dilaton coupling satisfies $a^2 = 1/3$.

**Metric:** Fully analytic. In standard coordinates: $ds^2 = -U(r)dt^2 + dr^2/U(r) + e^{2V(r)}dx_i^2$, where $U(r)$ and $V(r)$ are known closed-form functions of $(r, r_h, Q)$. Domain wall gauge conversion: $A(z) = V(r(z))$, $f(z) = U(r(z))/e^{2V(r(z))}$.

**Key parameters:** Chemical potential $\mu$, dilaton coupling $a^2=1/3$ (fixed), optionally momentum relaxation rate $\beta$ (from added linear axions in the EMDA version).

**Boundary physics:** **$T$-linear resistivity** (strange metal behavior) — the defining feature. The IR geometry is conformal to AdS$_2\times\mathbb{R}^2$, with effective hyperscaling violation $\theta/z = -1$. Unlike RN-AdS, the **entropy density vanishes** as $T\to 0$, resolving the extremal entropy problem. Linear specific heat (Sommerfeld behavior).

**IR behavior:** Conformal to AdS$_2\times\mathbb{R}^{d-1}$ with a mild null singularity rather than the smooth AdS$_2$ throat of RN-AdS. Zero-temperature entropy density $s(T=0)=0$.

**Distinctness:** YES. While formally a member of the EMD class, the Gubser-Rocha model has rare fully analytic solutions and captures strange-metal transport that no other family in the catalog reproduces.

**References:** Gubser, Rocha (2010) arXiv:0911.2898; Davison, Schalm, Zaanen (2014) arXiv:1311.2451.

---

### Family 9: Charged hyperscaling-violating Lifshitz (charged EMD)

**Standard notation:** Charged hvLif black brane in Einstein-Maxwell-Dilaton theory.

**Metric:** 
$$ds^2 = r^{-2(d-\theta)/d}\left[-r^{-2(z-1)}f(r)\,dt^2 + \frac{dr^2}{f(r)} + dx_i^2\right]$$

$$f(r) = 1 - (1+Q^2)\!\left(\frac{r}{r_h}\right)^{d+z-\theta} + Q^2\!\left(\frac{r}{r_h}\right)^{2(d+z-\theta-1)}$$

**Domain wall gauge:** $e^{2A} = r^{-2(d-\theta)/d}$ for the spatial part, with $dz_{\rm DW} = r^{(d-\theta)/d}\,dr/\sqrt{f(r)}$. The warp factor: $A(z) = -\frac{d-\theta}{d}\ln r(z)$.

**Key parameters:** Dynamical exponent $z$, hyperscaling violation $\theta$, charge $Q$, dilaton couplings $(\eta, \lambda)$ in $V = V_0 e^{\eta\phi}$, $Z = Z_0 e^{\lambda\phi}$. Null energy conditions: $(d-\theta)(d(z-1)-\theta)\geq 0$ and $(z-1)(d+z-\theta)\geq 0$.

**Boundary physics:** Compressible quantum matter with anomalous scaling. Entropy $S\sim T^{(d-\theta)/z}$, entanglement area-law violation for $d-1<\theta<d$. The case $\theta = d-1$ mimics a **hidden Fermi surface**. Charged transport with anomalous power-law scaling.

**IR behavior:** For the charged extremal case, the near-horizon can develop an emergent AdS$_2\times\mathbb{R}^d$ throat or remain hvLif depending on parameters. The geometry is generically IR-incomplete due to the running dilaton.

**Distinctness:** YES — extends the existing `hyperscaling` family by adding finite charge. Interpolates between RN-AdS ($z=1, \theta=0$), neutral hvLif ($Q=0$), and Lifshitz ($\theta=0$).

**References:** Gouteraux, Kiritsis (2011) arXiv:1107.2116; Dong, Harrison, Kachru, Torroba, Wang (2012) arXiv:1201.1905; Charmousis, Gouteraux, Kim, Kiritsis, Meyer (2010) arXiv:1005.4690.

---

### Family 10: Born-Infeld AdS black brane

**Standard notation:** Einstein-Born-Infeld-AdS (EBI-AdS) black brane.

**Metric (planar, $D=d+2$ bulk):**
$$h(r) = \frac{r^2}{L^2} - \frac{m_0}{r^{d-1}} + \frac{4\beta^2 r^2}{(d+1)d}\!\left[1 - \sqrt{1 + \frac{d(d-1)q^2}{2\beta^2 r^{2d}}}\right] + \frac{2(d-1)q^2}{(d+1)r^{2(d-1)}}\;{}_2F_1\!\left[\tfrac{d-1}{2d},\tfrac{1}{2},\tfrac{3d-1}{2d},-\tfrac{d(d-1)q^2}{2\beta^2 r^{2d}}\right]$$

with the standard holographic form $ds^2 = (r^2/L^2)[-h(r)dt^2 + dx_i^2] + L^2 dr^2/(r^2 h(r))$.

**Domain wall gauge:** Same as RN-AdS conversion: $A(z) = -\ln(z/L)$ near boundary, $f(z) = h(r(z))$. The hypergeometric terms make the $z(r)$ integral non-elementary.

**Key parameters:** BI parameter $\beta$ (dimension of mass; $\beta = 1/(2\pi\alpha')$ in string theory), charge $q$, mass $m_0$. **Limit $\beta\to\infty$** recovers RN-AdS (Maxwell electrodynamics).

**Boundary physics:** Modified finite-density holographic matter with nonlinear electromagnetic response. Exhibits **van der Waals-type phase transitions**, reentrant phase transitions, and triple-point behavior absent in RN-AdS. The BI nonlinearity regularizes the electric field at $r=0$.

**IR behavior:** Non-extremal: standard Rindler horizon. Extremal: modified AdS$_2$ throat with $\beta$-dependent radius.

**Distinctness:** YES — one-parameter deformation of RN-AdS with qualitatively richer thermodynamic phase structure.

**References:** Cai, Pang, Wang (2004) hep-th/0410158; Dey (2004); Gunasekaran, Kubizňák, Mann (2012) arXiv:1208.6251.

---

### Family 11: Charged Lifshitz black brane

**Standard notation:** Charged Lifshitz black brane (asymptotically Lifshitz at finite density).

**Metric:**
$$ds^2 = -\left(\frac{r}{\ell}\right)^{2z_{\rm dyn}} f(r)\,dt^2 + \frac{\ell^2}{r^2 f(r)}\,dr^2 + \frac{r^2}{\ell^2}\,dx_i^2$$

$$f(r) = 1 - \frac{M}{r^{d+z_{\rm dyn}-1}} + \frac{Q^2}{r^{2(d+z_{\rm dyn}-2)}}$$

**Domain wall gauge:** Define $dz_{\rm DW} = \ell\,dr/(r\sqrt{f})$. Then $e^{2A} = (r/\ell)^2$ for the spatial part. The warp factor involves $z_{\rm dyn}$-dependent powers through the $t$-component.

**Key parameters:** Dynamical exponent $z_{\rm dyn}$, charge density $\rho$ (or $Q$), temperature $T$. Phase structure depends qualitatively on whether $z_{\rm dyn}<2$, $=2$, or $>2$.

**Boundary physics:** Non-relativistic CFT at finite density. At extremality, the near-horizon can re-emerge as AdS$_2\times\mathbb{R}^{d-1}$ for $z_{\rm dyn}=2$, producing quantum-critical charge transport distinct from neutral Lifshitz.

**Distinctness:** YES — extends the existing `lifshitz` family by adding charge, qualitatively changing the extremal limit and transport.

**References:** Tarrio, Vandoren (2011) arXiv:1105.6335; Brynjolfsson, Danielsson, Nattermann, Ohl (2010) arXiv:0908.2611.

---

## Modified gravity families probe finite-coupling and beyond-Einstein physics

### Family 12: Gauss-Bonnet AdS black brane

**Standard notation:** Einstein-Gauss-Bonnet (EGB) planar black brane. **Requires $d+1\geq 5$ bulk dimensions ($d\geq 4$ boundary).**

**Metric (planar horizon):**
$$ds^2 = -r^2 h(r)\,dt^2 + \frac{dr^2}{r^2 h(r)} + r^2\,dx_i^2$$

$$h(r) = \frac{1}{2\tilde\alpha}\left[1 - \sqrt{1 - 4\lambda_{\rm GB}\!\left(1 - \frac{r_h^d}{r^d}\right)}\right]$$

where $\lambda_{\rm GB} = (d-2)(d-3)\alpha_{\rm GB}/L^2$ is the dimensionless coupling and $\tilde\alpha = (d-2)(d-3)\alpha_{\rm GB}$.

**Domain wall gauge:** Near boundary: $A(z) = -\ln(z/L_{\rm eff})$ with **effective AdS radius** $L_{\rm eff}^2 = L^2[1+\sqrt{1-4\lambda_{\rm GB}}]/2$. The square-root structure in $h(r)$ carries through to $f(z)$.

**Key parameters:** $\lambda_{\rm GB}$ (dimensionless GB coupling). Causality bound: $\lambda_{\rm GB}\leq 9/100$ for $d=4$. The shear viscosity ratio becomes $\eta/s = \frac{1}{4\pi}[1-4\lambda_{\rm GB}]$ in $d=4$, **violating the KSS bound** for $\lambda_{\rm GB}>0$.

**Boundary physics:** Dual CFT with $a\neq c$ central charges (finite 't Hooft coupling corrections). Modifies quasinormal mode spectra, complexity growth rates, and thermalization dynamics. The GB coupling parametrizes $1/\lambda_{\rm 't\,Hooft}$ corrections to strongly coupled plasma.

**IR behavior:** Regular Rindler horizon. Temperature $T = dr_h/(4\pi L_{\rm eff}^2)$ with GB-modified coefficient. Entropy density $s\propto r_h^{d-1}(1 + 2(d-1)\tilde\alpha/((d-3)r_h^2))$ departs from the area law.

**Distinctness:** YES — the square-root blackening factor and $a\neq c$ physics have no counterpart in any existing family.

**References:** Cai (2002) hep-th/0109133; Brigante, Liu, Myers, Shenker, Yaida (2008) arXiv:0712.0805 and arXiv:0802.3318; Buchel, Myers, Sinha (2009) arXiv:0812.2521.

---

### Family 13: $f(R)$ gravity AdS black holes

**Standard notation:** $f(R) = R + \alpha R^2$ (Starobinsky-type) AdS black holes.

**Key result:** For constant-curvature solutions ($R = R_0$), the metric is formally AdS-Schwarzschild with **renormalized constants**: $G_{\rm eff} = G/(1+2\alpha R_0)$, $L_{\rm eff}$ shifted by $\alpha$. The conformal mapping to Einstein frame introduces a massive scalar $\phi$ with $m_\phi^2 = 1/(6\alpha)$, dual to a scalar operator of dimension $\Delta(m_\phi)$.

**Domain wall gauge:** Same as `ads` family but with $L\to L_{\rm eff}$ and $G\to G_{\rm eff}$. The Wald entropy $S = \frac{A}{4G_{\rm eff}}(1+2\alpha R_0)$ differs from Bekenstein-Hawking.

**Distinctness:** MARGINAL — constant-curvature solutions are metrically identical to AdS-Schwarzschild up to parameter redefinition. Non-constant-curvature solutions (where $R(r)$ varies) are genuinely distinct but typically numerical.

**References:** Nojiri, Odintsov (2002) hep-th/0204112; Moon, Myung, Son (2011) arXiv:1101.1153; Sotiriou, Faraoni (2010) arXiv:0805.1726.

---

### Family 14: Hořava-Lifshitz gravity black holes

**Standard notation:** Hořava-Lifshitz (HL) black holes — UV-complete gravity with anisotropic scaling $z_{\rm HL}$.

**Key solutions (4D, Kehagias-Sfetsos):**
$$f(r) = 1 + \omega r^2 - \omega r^2\sqrt{1 + 4M/(\omega r^3)}$$

This square-root structure resembles GB gravity. The parameter $\omega$ encodes HL couplings; the GR limit is $\omega\to\infty$ where $f\to 1-2M/r$.

**Domain wall gauge:** Standard conversion for AdS solutions. The blackening factor's square-root structure makes $z(r)$ non-elementary.

**Key parameters:** $\lambda$ (running coupling; GR at $\lambda=1$), $\mu$ (HL mass scale), $z_{\rm HL}=3$ in 3+1D UV. **Distinct from Lifshitz spacetime:** HL is a modified *gravity theory*, while Lifshitz geometries are *solutions* in Einstein gravity with special matter.

**Boundary physics:** Lorentz-violating boundary theory with anisotropic dispersion $\omega^2\sim k^{2z}$. "Universal horizons" can differ from Killing horizons due to broken Lorentz invariance.

**Distinctness:** YES — fundamentally different gravitational dynamics (higher spatial derivatives, foliation structure). However, for specific couplings, 5D HL solutions coincide with GB solutions.

**References:** Hořava (2009) arXiv:0901.3775; Lü, Mei, Pope (2009) arXiv:0904.1595; Cai, Cao, Ohta (2009) arXiv:0904.3670.

---

## Momentum-relaxation geometries capture realistic transport

### Family 15: Massive gravity AdS black brane (dRGT)

**Standard notation:** Holographic massive gravity (de Rham-Gabadadze-Tolley) in AdS.

**Metric (planar, $d+2$ dimensions):**
$$h(r) = 1 - \frac{m_0}{r^{d-1}} + \frac{q^2}{r^{2(d-1)}} + \frac{r^2}{L^2} + c_1 m_g^2 r + c_2 m_g^2$$

where $m_g$ is the graviton mass and $c_1, c_2$ are dimensionless couplings from the dRGT potential. The massive gravity terms — **linear in $r$ ($c_1 m_g^2 r$) and constant ($c_2 m_g^2$)** — are polynomial corrections to the RN-AdS blackening factor.

**Domain wall gauge:** $A(z) = -\ln(z/L)$ near boundary (UV unmodified), $f(z) = h(r(z))$. The massive gravity terms do not change asymptotics but modify the interior and horizon structure.

**Key parameters:** Graviton mass $m_g$, couplings $c_1, c_2$, charge $q$. Momentum relaxation rate $\tau^{-1}\sim m_g^2$.

**Boundary physics:** **Finite DC conductivity** — unlike RN-AdS which has $\sigma_{\rm DC}=\infty$ due to translational invariance. Drude peak at low $\omega$ with width $\sim m_g^2$. Models strongly coupled systems with disorder or lattice effects. $\sigma_{\rm DC} = 1 + \mu^2/(m_g^2 r_h)$.

**IR behavior:** The $c_1 m_g^2 r$ term can change the number of horizons (zero, one, or two), altering the causal structure relative to RN-AdS. Modified Hawking-Page transition temperature.

**Distinctness:** YES — breaks translational symmetry at the level of the gravitational sector. Technically related to (but physically distinct from) the linear axion model (Family 16).

**References:** Vegh (2013) arXiv:1301.0537; Davison (2013) arXiv:1306.5792; Blake, Tong (2013) arXiv:1308.4970; Cai, Hu, Pan, Zhang (2015) arXiv:1409.2369.

---

### Family 16: Linear axion (Andrade-Withers) model

**Standard notation:** Holographic linear axion model for momentum relaxation.

**Action:** Einstein gravity + cosmological constant + $d-1$ massless scalars $\psi_I = \alpha\, x^I$.

**Metric (neutral, $d+1=4$):**
$$h(r) = 1 - \frac{r_h^3}{r^3} - \frac{\alpha^2}{2r^2}\!\left(1 - \frac{r_h}{r}\right)$$

The metric remains **homogeneous and isotropic** despite the spatially-dependent axion profiles — the key insight of Andrade-Withers. This is possible because the stress tensor of the linear axions is spatially constant.

**Domain wall gauge:** $A(z) = -\ln(z/L)$ (identical to AdS-Schwarzschild), $f(z) = h(r(z))$. The warp factor is **unmodified**; only the blackening factor receives $\alpha^2$-corrections.

**Key parameters:** Axion gradient $\alpha$ (momentum relaxation rate), optionally charge $\mu$ (when U(1) gauge field is added). For $d=3$, equivalent to massive gravity with $m_g^2 = \alpha^2/2$.

**Boundary physics:** Finite DC conductivity $\sigma_{\rm DC} = r_h^{d-2} + \mu^2/(\alpha^2 + \ldots)$, Drude transport, coherent–incoherent transition as $\alpha/T$ varies, metal-insulator transitions possible with extensions.

**IR behavior:** Regular horizon. Temperature $T = \frac{1}{4\pi}[d\,r_h/L^2 - \alpha^2 L^2/(2r_h)]$. The axion parameter reduces $T$ relative to pure AdS-Schwarzschild at fixed $r_h$. At $T=0$: extremal geometry with AdS$_2\times\mathbb{R}^{d-1}$.

**Distinctness:** PARTIAL — same $A(z)$ as `ads`, modification only in $f(z)$. However, the broken translational symmetry produces qualitatively distinct boundary transport (finite $\sigma_{\rm DC}$), making it a physically important extension.

**References:** Andrade, Withers (2014) arXiv:1311.5157; Baggioli, Pujolàs (2015) arXiv:1411.1003; Baggioli, Kim, Li, Li (2021) arXiv:2101.01892.

---

## Confinement and QCD-motivated geometries

### Family 17: Einstein-dilaton / IHQCD

**Standard notation:** Improved Holographic QCD (IHQCD) — Einstein-dilaton gravity with engineered potential.

**Action (5D):** $S = \frac{1}{16\pi G_5}\int d^5x\sqrt{g}\left[R - \frac{4}{3}(\partial\phi)^2 + V(\phi)\right]$, with $\phi$ the dilaton related to 't Hooft coupling $\lambda = e^\phi$.

**Metric in domain wall gauge (natural coordinates):**
$$ds^2 = e^{2A(z)}[-f(z)dt^2 + dx_i^2] + \frac{dz^2}{f(z)}$$

This is the **native coordinate system** for IHQCD. The UV asymptotics: $A(z)\approx -\ln(z/L) - \frac{4}{9}b_0^2(\ln(z/L))^2 + \ldots$ where $b_0$ is the one-loop $\beta$-function coefficient. The logarithmic corrections encode **asymptotic freedom**.

**IR asymptotics:** For confinement with linear Regge trajectories ($m_n^2\sim n$), the dilaton potential requires $V(\phi)\sim \phi^{2/3}e^{4\phi/(3\sqrt{d-1})}$, giving $A(z)\sim -c\,z^{2/3}$ in the deep IR (up to logs).

**Blackening factor:** $f''(z) + d\,A'(z)f'(z) = 0$ with $f(0)=1$, $f(z_h)=0$, yielding:
$$f(z) = 1 - \frac{\int_0^z e^{-dA(z')}dz'}{\int_0^{z_h} e^{-dA(z')}dz'}$$

**Key parameters:** $b_0$ ($\beta$-function coefficient), dilaton potential shape (controlling IR behavior), $\Lambda_{\rm QCD}$ scale, temperature $T$.

**Boundary physics:** **Confinement** (area-law Wilson loops, linear quark potential), linear Regge trajectories, glueball spectra matching lattice QCD, **first-order Hawking-Page deconfinement transition** at $T_c\approx 235$ MeV, equation of state matching lattice data, bulk viscosity peaked near $T_c$.

**Distinctness:** YES — genuinely distinct. The running dilaton backreacts on $A(z)$ producing UV log corrections and power-law IR growth absent in all other families.

**References:** Gürsoy, Kiritsis (2008) arXiv:0707.1324; Gürsoy, Kiritsis, Nitti (2008) arXiv:0707.1349; Gubser, Nellore (2008) arXiv:0804.0434; Gürsoy, Kiritsis, Mazzanti, Nitti (2009) arXiv:0812.0792.

---

### Family 18: AdS soliton (Horowitz-Myers confining geometry)

**Standard notation:** AdS soliton — double Wick rotation of AdS-Schwarzschild.

**Metric:**
$$ds^2 = \frac{r^2}{L^2}\!\left[-dt^2 + dx_i^2 + g(r)\,d\chi^2\right] + \frac{L^2\,dr^2}{r^2 g(r)}, \qquad g(r) = 1 - \left(\frac{r_0}{r}\right)^d$$

where $\chi$ is compactified with period $\beta_\chi = 4\pi L^2/(d\,r_0)$ for regularity at the tip $r=r_0$.

**Domain wall gauge:** The metric does **not** fit the standard isotropic domain wall ansatz because the compactified direction $\chi$ has a different warp factor from the non-compact $x_i$. For the effective $(d-1)$-dimensional boundary theory (after KK reduction on $\chi$): $A(z) = \ln(r(z)/L)$, **$f(z) = 1$ (no horizon)**. The geometry smoothly caps off at $z_{\rm tip}$ where the $\chi$-circle shrinks to zero.

**Key parameters:** $r_0$ (confinement scale), $\beta_\chi$ (compact circle period). **No horizon** — this is a zero-temperature, horizonless geometry.

**Boundary physics:** Dual to a **confined phase** of gauge theory compactified on $S^1$ with antiperiodic fermion boundary conditions. Mass gap, discrete glueball spectrum, area law for spatial Wilson loops. The **Hawking-Page transition** between AdS soliton and planar AdS-Schwarzschild is the holographic confinement/deconfinement transition.

**IR behavior:** At $r\to r_0$ (the tip), $g(r)\to 0$ and the $\chi$-circle shrinks smoothly to zero — a cigar-like cap with no singularity. This smooth cap provides the mass gap.

**Distinctness:** YES — topologically distinct (horizonless, compact spatial direction, cigar geometry).

**References:** Horowitz, Myers (1998) hep-th/9808079; Witten (1998) hep-th/9803131.

---

### Family 19: Backreacted soft-wall holographic QCD

**Standard notation:** Dynamical/backreacted soft-wall model.

The original KKSS soft-wall (Karch, Katz, Son, Stephanov 2006, hep-ph/0602229) uses pure AdS geometry with a non-dynamical dilaton $\Phi(z)=(cz)^2$ — this is **not** a new geometry family. However, backreacted versions where the dilaton modifies $A(z)$ are distinct:

**Batell-Gherghetta (2008):** In Einstein frame, $A_E(z) = -\ln(z/L) - \frac{2}{3}(cz)^2$. The quadratic correction to $A(z)$ produces the soft wall through geometry rather than a probe coupling.

**He-Huang-Yan (2013):** $A(z) = -\ln(z/L) + cz^2$ with positive $c$ (favored by Polyakov loop data).

**Key parameters:** Soft-wall scale $c$ (related to $\Lambda_{\rm QCD}$, sets Regge slope $\sigma'$).

**Boundary physics:** Linear Regge trajectories $m_n^2\propto n$, improving on the hard-wall $m_n^2\propto n^2$. Chiral symmetry breaking when coupled to a tachyon field.

**Distinctness:** PARTIAL — overlaps with the IHQCD family (Family 17) when the dilaton potential is derived self-consistently, but is often a simpler sub-class with a specific phenomenological ansatz for $\Phi(z)$.

**References:** Karch, Katz, Son, Stephanov (2006) hep-ph/0602229; Batell, Gherghetta (2008) arXiv:0801.4383; He, Huang, Yan (2013) arXiv:1104.0940.

---

## Hairy and non-Abelian black holes

### Family 20: Holographic superconductor (Hartnoll-Herzog-Horowitz)

**Standard notation:** HHH s-wave holographic superconductor (Abelian-Higgs black hole in AdS).

**Action (4D bulk):** $S = \int d^4x\sqrt{-g}\left[R + 6/L^2 - \frac{1}{4}F^2 - |D\Psi|^2 - m^2|\Psi|^2\right]$, with $D_\mu = \nabla_\mu - iqA_\mu$.

**Metric (with backreaction):**
$$ds^2 = -g(r)e^{-\chi(r)}dt^2 + \frac{dr^2}{g(r)} + r^2\,dx_i^2$$

**Solutions are numerical.** Above $T_c$: $\Psi=0$, reduces to RN-AdS. Below $T_c$: coupled ODEs for $g(r)$, $\chi(r)$, $\Psi(r)$, $A_t(r)$ are solved by shooting from the horizon. Near boundary: $\Psi\sim \Psi_1 z^{\Delta_-} + \Psi_2 z^{\Delta_+}$ with $\Delta_\pm = d/2\pm\sqrt{d^2/4 + m^2 L^2}$.

**Key parameters:** Scalar mass $m^2$ (must satisfy BF bound), charge $q$, critical temperature $T_c\propto\mu$ (or $\rho^{1/(d-1)}$).

**Boundary physics:** **Second-order phase transition** to a superconducting state with condensate $\langle\mathcal{O}\rangle\propto (1-T/T_c)^{1/2}$ (mean-field exponent). Infinite DC conductivity below $T_c$, spectral gap $\omega_g\approx 8T_c$ in $\sigma(\omega)$, Meissner effect.

**IR behavior:** Below $T_c$ at $T\to 0$: the geometry flows from AdS$_4$ UV to an emergent Lifshitz-like or new AdS$_4$ IR rather than the extremal RN-AdS. The scalar hair resolves the extremal entropy problem.

**Distinctness:** YES — spontaneous symmetry breaking below $T_c$ produces a hairy black hole with modified metric and gauge field absent in all other families.

**References:** Hartnoll, Herzog, Horowitz (2008) arXiv:0803.3295, arXiv:0810.1563; Horowitz (2010) arXiv:1002.1722.

---

### Family 21: Einstein-Yang-Mills AdS black holes

**Standard notation:** EYM-AdS "colored" black holes with SU(2) gauge field hair.

**Metric (spherical, 4D):**
$$ds^2 = -N(r)\sigma^2(r)\,dt^2 + \frac{dr^2}{N(r)} + r^2\,d\Omega^2$$

with coupled ODEs for $N(r)$, $\sigma(r)$, and the YM gauge function $\omega(r)$. **Solutions are generically numerical**, obtained by shooting. For the embedded Abelian (purely magnetic) solution, the metric resembles RN-AdS with magnetic charge.

**Key feature:** In AdS, hairy EYM black holes can be **stable** (unlike asymptotically flat), providing genuine non-Abelian hair outside the horizon. The hairy solutions are labeled by the number of nodes $n$ of $\omega(r)$.

**Boundary physics:** YM condensate on boundary models **p-wave superconductors** (Gubser-Pufu, arXiv:0805.2960). Phase transitions between embedded RN-AdS and hairy solutions.

**Distinctness:** YES — non-Abelian gauge structure not captured by Einstein-Maxwell. However, requiring spherical symmetry (not planar) limits domain-wall-gauge compatibility.

**References:** Bjoraker, Hosotani (2000) hep-th/0002098; Winstanley (2009) arXiv:0801.0527; Baxter, Helbling, Winstanley (2008) arXiv:0708.2356.

---

## Topological, lower-dimensional, and dynamical geometries

### Family 22: Topological black holes (hyperbolic horizon, $\kappa=-1$)

**Standard notation:** Hyperbolic AdS black hole (Birmingham-Vanzo topology).

**Metric:**
$$ds^2 = -h(r)\,dt^2 + \frac{dr^2}{h(r)} + r^2\,d\Sigma_{-1,d-1}^2, \qquad h(r) = -1 + \frac{r^2}{L^2} - \frac{\omega_d}{r^{d-2}}$$

where $d\Sigma_{-1}^2$ is the metric on $\mathbb{H}^{d-1}$. The crucial **$-1$** (versus $+1$ for spherical) changes thermodynamics qualitatively.

**Domain wall gauge:** Requires replacing flat $dx_i^2$ with $d\Sigma_{-1}^2$. The generalized form $ds^2 = e^{2A(z)}[-f(z)dt^2 + d\Sigma_{-1}^2] + dz^2/f(z)$ accommodates this.

**Massless hyperbolic black hole ($\omega_d=0$):** $h(r) = -1 + r^2/L^2$, horizon at $r=L$, **$T=0$** — a zero-temperature ground state with **nonzero entropy density**, fundamentally different from all other $T=0$ states in the catalog.

**Boundary physics:** CFT on $\mathbb{H}^{d-1}$, related to the Rindler decomposition of flat-space CFT. Entanglement entropy across Rindler horizons. Near-extremal regime controlled by conformal quantum mechanics (AdS$_2$).

**Distinctness:** YES — different horizon topology, qualitatively distinct thermodynamics, novel $T=0$ ground state.

**References:** Birmingham (1999) hep-th/9808032; Vanzo (1997) gr-qc/9705004; Emparan (1999) hep-th/9906040.

---

### Family 23: Vaidya-AdS (dynamical null shell)

**Standard notation:** Vaidya-AdS (time-dependent collapsing shell).

**Metric (Eddington-Finkelstein):**
$$ds^2 = -\!\left(\frac{r^2}{L^2} - \frac{m(v)}{r^{d-2}}\right)dv^2 + 2\,dv\,dr + r^2\,dx_i^2$$

with $m(v) = \frac{M}{2}(1+\tanh(v/v_0))$ (smooth shell) or $m(v) = M\,\Theta(v)$ (sharp shell).

**⚠️ Domain wall gauge: INAPPLICABLE.** The geometry is intrinsically time-dependent. For $v\ll 0$: pure AdS. For $v\gg 0$: AdS-Schwarzschild. At intermediate times, no static gauge exists.

**Boundary physics:** **Thermalization after quantum quench** — the defining application. Entanglement entropy grows as $S_A\sim v_E\,s_{\rm eq}\,t$ (linear "entanglement tsunami" regime) with entanglement velocity $v_E$, then saturates. UV thermalizes before IR (top-down thermalization).

**Distinctness:** YES — the only intrinsically time-dependent family. Captures non-equilibrium physics inaccessible to all static families.

**References:** Balasubramanian et al. (2011) arXiv:1012.4753, arXiv:1103.2683; Liu, Suh (2014) arXiv:1305.7244.

---

### Family 24: Warped AdS$_3$ (TMG black holes)

**Standard notation:** Warped BTZ in Topologically Massive Gravity.

The warped AdS$_3$ metric has isometry SL(2,$\mathbb{R}$)$\times$U(1) (reduced from SL(2,$\mathbb{R}$)$\times$SL(2,$\mathbb{R}$) of ordinary AdS$_3$) with a warping parameter $\nu$ related to the gravitational Chern-Simons coupling $\mu\ell$.

**⚠️ Domain wall gauge: NON-TRIVIAL.** The metric has an off-diagonal $g_{t\theta}$ cross-term from the shift function $N^\theta(r)$ that fundamentally obstructs standard diagonal domain wall form.

**Boundary physics:** Dual **warped CFT** (non-relativistic 2D). Warped Cardy formula reproduces black hole entropy. Related to near-horizon extremal Kerr via Kerr/CFT correspondence.

**Distinctness:** YES — specific to 3D parity-violating massive gravity. Qualitatively distinct from BTZ.

**References:** Anninos, Li, Padi, Song, Strominger (2009) arXiv:0807.3040; Detournay, Hartman, Hofman (2012) arXiv:1210.0539.

---

## Numerical-only families with well-defined ODEs

### Family 25: Q-lattice / Stückelberg holographic models

**Standard notation:** Holographic Q-lattice (Donos-Gauntlett).

**Action (4D):** Einstein-Maxwell + charged complex scalar $\Phi = \phi(r)e^{ikx}$ — the spatial dependence factorizes, preserving homogeneous metric ODEs while breaking translation invariance.

**Metric:** $ds^2 = e^{2A(z)}[-f(z)dt^2+dx_i^2]+dz^2/f(z)$ with $A(z)$, $f(z)$ solved numerically from coupled ODEs. **UV:** $A(z)\to -\ln(z/L)$. **IR:** varies — AdS$_2\times\mathbb{R}^2$ (metallic), AdS$_3\times\mathbb{R}$ (insulating with hard gap), or Lifshitz-like.

**Key parameters:** Lattice wavevector $k$, scalar mass $m^2$, scalar charge $q$, chemical potential $\mu$.

**Boundary physics:** **Metal-insulator transitions**, coherent/incoherent transport crossover, Drude conductivity in metallic phases. "Boomerang" RG flows at zero temperature.

**Distinctness:** YES — translation-breaking mechanism is qualitatively different from massive gravity or axions. Rich IR landscape.

**References:** Donos, Gauntlett (2014) arXiv:1311.3292, arXiv:1401.5077.

---

### Family 26: Holographic Weyl semimetal

**Standard notation:** Holographic Weyl semimetal (hWSM) — EMDA model with Chern-Simons coupling.

**Metric:** Numerical solutions in domain wall gauge. The system undergoes a **topological quantum phase transition** at critical $M/b$ between a topological Weyl semimetal phase (nonzero anomalous Hall conductivity $\sigma_{\rm AHE}$) and a trivial phase ($\sigma_{\rm AHE}=0$).

**Distinctness:** YES — requires an axial gauge field with Chern-Simons term absent in all other families. The topological phase transition has no analog elsewhere.

**References:** Landsteiner, Liu, Sun (2016) arXiv:1511.05505; Landsteiner, Liu, Sun (2020) arXiv:1911.07978.

---

## Negative controls and edge cases

### Family 27: de Sitter / Schwarzschild-dS

**Metric:** $f(r) = 1 - 2M/r^{d-2} - r^2/L_{\rm dS}^2$ (positive cosmological constant).

**⚠️ Domain wall gauge:** Formally writable but physically meaningless for standard holography — the boundary is spacelike (future infinity $\mathscr{I}^+$), not timelike. No conformal boundary in the AdS sense. dS/CFT (Strominger 2001, hep-th/0106113) is speculative and the dual CFT is generically **non-unitary**.

**Purpose:** Negative control — should produce no standard holographic physics.

**References:** Strominger (2001) hep-th/0106113; Anninos (2012) arXiv:1205.3855.

---

### Family 28: Flat space / Minkowski

$A(z)=0$, $f(z)=1$. No warping, no horizon, no holographic boundary. The trivial $L\to\infty$ limit. Serves as a **sanity-check negative control**.

---

## Three families that resist domain wall gauge

Several physically interesting geometries cannot fit the RINGEST domain wall ansatz without significant modification:

- **Janus geometries** (Bak, Gutperle, Hirano 2003, hep-th/0304129): The metric depends on both a radial and a spatial coordinate, breaking the 1D radial-ODE structure. Dual to interface CFTs with spatially varying coupling.
- **Global AdS-Schwarzschild (spherical horizon):** Requires curved spatial sections $d\Omega^2$ incompatible with flat $dx_i^2$. The Hawking-Page transition it hosts is topologically distinct from the planar case.
- **Kasner-AdS interiors** (Frenkel, Hartnoll, Kruthoff, Shi 2020, arXiv:2004.01192): Trans-horizon geometry where the radial coordinate becomes timelike. Relevant for black hole interior/singularity studies but lies beyond the boundary-to-horizon domain of the pipeline.

These could be incorporated with a generalized metric ansatz or treated as special post-processing cases.

---

## How the 18 new families organize by boundary physics

The full expanded catalog of **24 families** (6 existing + 18 new) covers the following physical regimes, with each new family producing qualitatively distinct boundary observables:

| Regime | Families | Key distinguishing observable |
|---|---|---|
| Finite density (relativistic) | **RN-AdS, Born-Infeld, Gubser-Rocha** | Extremal entropy, transport scaling, phase transitions |
| Finite density (non-relativistic) | **Charged EMD-hvLif, Charged Lifshitz** | Anomalous power-law transport, hidden Fermi surfaces |
| Momentum relaxation | **Massive gravity, Linear axion, Q-lattice** | Finite DC conductivity, Drude peaks, metal-insulator transitions |
| Confinement / QCD | **IHQCD, AdS soliton, Backreacted soft-wall** | Mass gap, Regge trajectories, deconfinement transitions |
| Spontaneous symmetry breaking | **Holographic superconductor, EYM** | Condensate, spectral gap, infinite DC conductivity |
| Modified gravity / finite coupling | **Gauss-Bonnet, $f(R)$, Hořava-Lifshitz** | $\eta/s$ violation, $a\neq c$, Lorentz violation |
| Topological / dynamical | **Hyperbolic BH, Vaidya-AdS, Warped AdS$_3$** | $T=0$ entropy, thermalization dynamics, warped CFT |
| Topological matter | **Weyl semimetal** | Anomalous Hall effect, topological QPT |
| Negative controls | **de Sitter, flat space** | No standard holographic physics |

## Prioritization for implementation

For the RINGEST ringdown pipeline, the highest-priority additions are those with **analytic $A(z)$ and $f(z)$** and **direct relevance to black hole physics**:

1. **RN-AdS** (Family 7) — most important single addition; finite density is essential and the metric is fully analytic
2. **Gauss-Bonnet** (Family 12) — analytic square-root blackening factor; directly modifies QNM spectra
3. **Massive gravity** (Family 15) — analytic polynomial corrections to $f(r)$; momentum relaxation
4. **Gubser-Rocha** (Family 8) — rare fully analytic EMD solution; strange metal physics
5. **Charged EMD-hvLif** (Family 9) — analytic power-law forms; broadest parameter coverage
6. **Linear axion** (Family 16) — analytic; simplest momentum relaxation model
7. **IHQCD** (Family 17) — native domain wall gauge; confinement physics
8. **Born-Infeld** (Family 10) — analytic (hypergeometric); tests nonlinear electrodynamics
9. **AdS soliton** (Family 18) — horizonless confining geometry; topologically distinct
10. **Holographic superconductor** (Family 20) — numerical but well-defined ODEs; phase-transition physics

Families 22–26 are valuable for completeness but require either generalized metric ansätze (curved spatial sections, time dependence, off-diagonal terms) or purely numerical integration.