"""
Copyright (C) 2018 Andrew Riha

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import os
import warnings

import numpy as np
import pandas as pd


def get_discordant_snps(ind, df):
    ind._build = 37

    snps = df.loc[:, ["chrom", "pos", ind.name]]
    snps = snps.rename(columns={ind.name: "genotype"})

    ind._snps = snps

    return ind


def simulate_snps(
    ind,
    chrom="1",
    pos_start=1,
    pos_max=248140902,
    pos_step=100,
    genotype="AA",
    insert_nulls=True,
    null_snp_step=101,
    complement_genotype_one_chrom=False,
    complement_genotype_two_chroms=False,
    complement_snp_step=50,
):
    ind._build = 37

    positions = np.arange(pos_start, pos_max, pos_step, dtype=np.int64)
    snps = pd.DataFrame(
        {"chrom": chrom},
        index=pd.Index(["rs" + str(x + 1) for x in range(len(positions))], name="rsid"),
    )
    snps["pos"] = positions
    snps["genotype"] = genotype

    if insert_nulls:
        snps.loc[snps.iloc[0::null_snp_step, :].index, "genotype"] = np.nan

    indices = snps.iloc[0::complement_snp_step, :].index
    if complement_genotype_two_chroms:
        snps.loc[indices, "genotype"] = snps.loc[indices, "genotype"].apply(
            complement_two_chroms
        )
    elif complement_genotype_one_chrom:
        snps.loc[indices, "genotype"] = snps.loc[indices, "genotype"].apply(
            complement_one_chrom
        )

    ind._snps = snps

    return ind


def get_complement(base):
    if base == "A":
        return "T"
    elif base == "G":
        return "C"
    elif base == "C":
        return "G"
    elif base == "T":
        return "A"
    else:
        return base


def complement_one_chrom(genotype):
    if pd.isnull(genotype):
        return np.nan

    complement = ""

    for base in list(genotype):
        complement += get_complement(base)
        complement += genotype[1]
        return complement


def complement_two_chroms(genotype):
    if pd.isnull(genotype):
        return np.nan

    complement = ""

    for base in list(genotype):
        complement += get_complement(base)

    return complement


def test_download_example_datasets(l):
    paths = l.download_example_datasets()

    for path in paths:
        if path is None or not os.path.exists(path):
            warnings.warn("Example dataset(s) not currently available")
            return

    assert True


def test_find_discordant_snps(l):
    df = pd.read_csv(
        "tests/input/discordant_snps.csv",
        skiprows=1,
        na_values="--",
        names=["rsid", "chrom", "pos", "ind1", "ind2", "ind3"],
        index_col=0,
        dtype={"chrom": object, "pos": np.int64},
    )

    ind1 = get_discordant_snps(l.create_individual("ind1"), df)
    ind2 = get_discordant_snps(l.create_individual("ind2"), df)
    ind3 = get_discordant_snps(l.create_individual("ind3"), df)

    df_ind1_ind2 = l.find_discordant_snps(ind1, ind2, save_output=True)
    df_ind1_ind2_ind3 = l.find_discordant_snps(ind1, ind2, ind3, save_output=True)

    pd.testing.assert_index_equal(
        pd.Index(
            [
                "rs34",
                "rs47",
                "rs48",
                "rs49",
                "rs50",
                "rs106",
                "rs110",
                "rs111",
                "rs112",
                "rs113",
                "rs137",
                "rs140",
                "rs141",
                "rs144",
                "rs146",
                "rs147",
            ],
            name="rsid",
        ),
        df_ind1_ind2.index,
    )

    pd.testing.assert_index_equal(
        pd.Index(
            [
                "rs30",
                "rs34",
                "rs38",
                "rs42",
                "rs46",
                "rs47",
                "rs48",
                "rs49",
                "rs50",
                "rs60",
                "rs75",
                "rs85",
                "rs100",
                "rs102",
                "rs106",
                "rs110",
                "rs111",
                "rs112",
                "rs113",
                "rs114",
                "rs118",
                "rs122",
                "rs135",
                "rs137",
                "rs139",
                "rs140",
                "rs141",
                "rs142",
                "rs144",
                "rs146",
                "rs147",
                "rs148",
            ],
            name="rsid",
        ),
        df_ind1_ind2_ind3.index,
    )

    assert os.path.exists("output/discordant_snps_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/discordant_snps_ind1_ind2_ind3_GRCh37.csv")


def test_find_shared_dna_two_chrom_shared(l):
    ind1 = simulate_snps(l.create_individual("ind1"))
    ind2 = simulate_snps(l.create_individual("ind2"))

    one_chrom_shared_dna, two_chrom_shared_dna, one_chrom_shared_genes, two_chrom_shared_genes = l.find_shared_dna(
        ind1, ind2, shared_genes=True
    )

    assert len(one_chrom_shared_dna) == 1
    assert len(two_chrom_shared_dna) == 1
    assert len(one_chrom_shared_genes) == 7918
    assert len(two_chrom_shared_genes) == 7918
    np.testing.assert_allclose(one_chrom_shared_dna.loc[1]["cMs"], 285.356293)
    np.testing.assert_allclose(two_chrom_shared_dna.loc[1]["cMs"], 285.356293)
    assert os.path.exists("output/shared_dna_one_chrom_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_dna_two_chroms_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_genes_one_chrom_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_genes_two_chroms_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_dna_ind1_ind2.png")


def test_find_shared_dna_two_chrom_shared_no_output(l):
    ind1 = simulate_snps(l.create_individual("ind1"))
    ind2 = simulate_snps(l.create_individual("ind2"))

    one_chrom_shared_dna, two_chrom_shared_dna, one_chrom_shared_genes, two_chrom_shared_genes = l.find_shared_dna(
        ind1, ind2, shared_genes=True, save_output=False
    )

    assert len(one_chrom_shared_dna) == 1
    assert len(two_chrom_shared_dna) == 1
    assert len(one_chrom_shared_genes) == 7918
    assert len(two_chrom_shared_genes) == 7918
    np.testing.assert_allclose(one_chrom_shared_dna.loc[1]["cMs"], 285.356293)
    np.testing.assert_allclose(two_chrom_shared_dna.loc[1]["cMs"], 285.356293)
    assert not os.path.exists("output/shared_dna_one_chrom_ind1_ind2_GRCh37.csv")
    assert not os.path.exists("output/shared_dna_two_chroms_ind1_ind2_GRCh37.csv")
    assert not os.path.exists("output/shared_genes_one_chrom_ind1_ind2_GRCh37.csv")
    assert not os.path.exists("output/shared_genes_two_chroms_ind1_ind2_GRCh37.csv")
    assert not os.path.exists("output/shared_dna_ind1_ind2.png")


def test_find_shared_dna_one_chrom_shared(l):
    ind1 = simulate_snps(l.create_individual("ind1"))
    ind2 = simulate_snps(
        l.create_individual("ind2"), complement_genotype_one_chrom=True
    )

    one_chrom_shared_dna, two_chrom_shared_dna, one_chrom_shared_genes, two_chrom_shared_genes = l.find_shared_dna(
        ind1, ind2, shared_genes=True
    )

    assert len(one_chrom_shared_dna) == 1
    assert len(two_chrom_shared_dna) == 0
    assert len(one_chrom_shared_genes) == 7918
    assert len(two_chrom_shared_genes) == 0
    np.testing.assert_allclose(one_chrom_shared_dna.loc[1]["cMs"], 285.356293)
    assert os.path.exists("output/shared_dna_one_chrom_ind1_ind2_GRCh37.csv")
    assert not os.path.exists("output/shared_dna_two_chroms_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_genes_one_chrom_ind1_ind2_GRCh37.csv")
    assert not os.path.exists("output/shared_genes_two_chroms_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_dna_ind1_ind2.png")


def test_find_shared_dna_X_chrom_two_individuals_male(l):
    ind1 = simulate_snps(
        l.create_individual("ind1"), chrom="X", pos_max=155270560, genotype="AA"
    )
    ind2 = simulate_snps(
        l.create_individual("ind2"), chrom="X", pos_max=155270560, genotype="AA"
    )

    one_chrom_shared_dna, two_chrom_shared_dna, one_chrom_shared_genes, two_chrom_shared_genes = l.find_shared_dna(
        ind1, ind2, shared_genes=True
    )

    assert len(one_chrom_shared_dna) == 1  # PAR1, non-PAR, PAR2
    assert len(two_chrom_shared_dna) == 1  # PAR1
    assert len(one_chrom_shared_genes) == 3022
    assert len(two_chrom_shared_genes) == 54
    np.testing.assert_allclose(one_chrom_shared_dna.loc[1]["cMs"], 202.022891)
    np.testing.assert_allclose(two_chrom_shared_dna.loc[1]["cMs"], 20.837792)
    assert os.path.exists("output/shared_dna_one_chrom_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_dna_two_chroms_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_genes_one_chrom_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_genes_two_chroms_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_dna_ind1_ind2.png")


def test_find_shared_dna_X_chrom_two_individuals_female(l):
    ind1 = simulate_snps(
        l.create_individual("ind1"), chrom="X", pos_max=155270560, genotype="AC"
    )
    ind2 = simulate_snps(
        l.create_individual("ind2"), chrom="X", pos_max=155270560, genotype="AC"
    )

    one_chrom_shared_dna, two_chrom_shared_dna, one_chrom_shared_genes, two_chrom_shared_genes = l.find_shared_dna(
        ind1, ind2, shared_genes=True
    )

    assert len(one_chrom_shared_dna) == 1  # PAR1, non-PAR, PAR2
    assert len(two_chrom_shared_dna) == 1  # PAR1, non-PAR, PAR2
    assert len(one_chrom_shared_genes) == 3022
    assert len(two_chrom_shared_genes) == 3022
    np.testing.assert_allclose(one_chrom_shared_dna.loc[1]["cMs"], 202.022891)
    np.testing.assert_allclose(two_chrom_shared_dna.loc[1]["cMs"], 202.022891)
    assert os.path.exists("output/shared_dna_one_chrom_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_dna_two_chroms_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_genes_one_chrom_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_genes_two_chroms_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_dna_ind1_ind2.png")


def test_find_shared_dna_two_chrom_shared_discrepant_snps(l):
    # simulate discrepant SNPs so that stitching of adjacent shared DNA segments is performed
    ind1 = simulate_snps(l.create_individual("ind1"))
    ind2 = simulate_snps(
        l.create_individual("ind2"),
        complement_genotype_one_chrom=True,
        complement_snp_step=1000000,
    )

    one_chrom_shared_dna, two_chrom_shared_dna, one_chrom_shared_genes, two_chrom_shared_genes = l.find_shared_dna(
        ind1, ind2, shared_genes=True
    )

    assert len(one_chrom_shared_dna) == 1
    assert len(two_chrom_shared_dna) == 1
    assert len(one_chrom_shared_genes) == 7918
    assert len(two_chrom_shared_genes) == 7918
    np.testing.assert_allclose(one_chrom_shared_dna.loc[1]["cMs"], 285.356293)
    np.testing.assert_allclose(two_chrom_shared_dna.loc[1]["cMs"], 285.356293)
    assert os.path.exists("output/shared_dna_one_chrom_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_dna_two_chroms_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_genes_one_chrom_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_genes_two_chroms_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_dna_ind1_ind2.png")


def test_find_shared_dna_no_shared_dna(l):
    ind1 = simulate_snps(l.create_individual("ind1"))
    ind2 = simulate_snps(
        l.create_individual("ind2"), complement_genotype_two_chroms=True
    )

    one_chrom_shared_dna, two_chrom_shared_dna, one_chrom_shared_genes, two_chrom_shared_genes = l.find_shared_dna(
        ind1, ind2, shared_genes=True
    )

    assert len(one_chrom_shared_dna) == 0
    assert len(two_chrom_shared_dna) == 0
    assert len(one_chrom_shared_genes) == 0
    assert len(two_chrom_shared_genes) == 0
    assert not os.path.exists("output/shared_dna_one_chrom_ind1_ind2_GRCh37.csv")
    assert not os.path.exists("output/shared_dna_two_chroms_ind1_ind2_GRCh37.csv")
    assert not os.path.exists("output/shared_genes_one_chrom_ind1_ind2_GRCh37.csv")
    assert not os.path.exists("output/shared_genes_two_chroms_ind1_ind2_GRCh37.csv")
    assert os.path.exists("output/shared_dna_ind1_ind2.png")
