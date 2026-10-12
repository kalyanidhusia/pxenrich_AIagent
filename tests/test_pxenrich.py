"""Unit + integration tests for the pxEnrich core.

Runs under pytest OR plain unittest:
    python -m pytest tests/ -q
    python -m unittest discover tests -v
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pxenrich.extraction import enrich_record  # noqa: E402
from pxenrich.models import AssertionStatus, DatasetRecord, Scope  # noqa: E402


def make(title="", desc=None, keywords=None, species="Homo sapiens") -> DatasetRecord:
    rec = DatasetRecord(accession="PXDTEST01", title=title, repository="PRIDE",
                        species=species, keywords=keywords, description=desc)
    return enrich_record(rec)


def get(rec, fieldname):
    return next(a for a in rec.assertions if a.field == fieldname)


class TestSubtypeExtraction(unittest.TestCase):
    def test_tnbc_asserted_from_title(self):
        rec = make("Proteomics of triple-negative breast cancer tumors from patients")
        a = get(rec, "subtype")
        self.assertEqual(a.status, AssertionStatus.ASSERTED)
        self.assertIn("TNBC", a.value)
        self.assertTrue(a.evidence_text)

    def test_tnbc_implies_receptor_negative(self):
        rec = make("Proteomics of triple-negative breast cancer tumors from patients")
        for f in ("er_status", "pr_status", "her2_status"):
            a = get(rec, f)
            self.assertEqual(a.status, AssertionStatus.ASSERTED, f)
            self.assertEqual(a.value, "negative", f)

    def test_mixed_subtypes(self):
        rec = make("Breast cancer study",
                   desc="Cohort spans luminal A, HER2-positive and triple-negative tumors")
        a = get(rec, "subtype")
        self.assertEqual(a.status, AssertionStatus.MIXED)

    def test_no_subtype_is_unknown_not_guessed(self):
        rec = make("Proteomic analysis of breast cancer tissue")
        a = get(rec, "subtype")
        self.assertEqual(a.status, AssertionStatus.UNKNOWN)
        self.assertIsNone(a.value)


class TestReceptorScope(unittest.TestCase):
    def test_her2_focus_is_not_cohort_status(self):
        """Studying HER2 must NOT become 'cohort is HER2-positive'."""
        rec = make("HER2 RIME experiment from breast cancer specimen",
                   keywords="ERBB2, HER2, RIME, breast cancer")
        a = get(rec, "her2_status")
        self.assertEqual(a.status, AssertionStatus.ABSTAINED)
        self.assertEqual(a.scope, Scope.STUDY_FOCUS)
        self.assertIsNone(a.value)

    def test_explicit_er_positive(self):
        rec = make("NF1-depleted ER+ breast cancers and CDK4/6 inhibitors")
        a = get(rec, "er_status")
        self.assertEqual(a.status, AssertionStatus.ASSERTED)
        self.assertEqual(a.value, "positive")

    def test_her2_low(self):
        rec = make("Proteomic landscape of HER2-low breast cancer biopsies")
        a = get(rec, "her2_status")
        self.assertEqual(a.status, AssertionStatus.ASSERTED)
        self.assertEqual(a.value, "low")


class TestOrganismContext(unittest.TestCase):
    def test_mouse_is_animal_model(self):
        rec = make("Mammary tumor proteomics", species="Mus musculus")
        a = get(rec, "organism_context")
        self.assertEqual(a.status, AssertionStatus.ASSERTED)
        self.assertIn("animal model", a.value)

    def test_human_cell_line_flagged(self):
        rec = make("Drug response in MCF-7 cells")
        a = get(rec, "organism_context")
        self.assertEqual(a.status, AssertionStatus.ASSERTED)
        self.assertIn("cell line", a.value)

    def test_patient_derived(self):
        rec = make("Tumor tissue from breast cancer patients")
        a = get(rec, "organism_context")
        self.assertIn("patient-derived", a.value)

    def test_keyword_only_breast_cancer_abstains(self):
        """E. coli biochemistry tagged 'breast cancer' must not be labeled a
        breast-cancer study."""
        rec = make("RAD51-BRC repeats interplay in homologous recombination",
                   keywords="BRCA2, RAD51, breast cancer, crosslinking",
                   species="Escherichia coli")
        a = get(rec, "disease_context")
        self.assertEqual(a.status, AssertionStatus.ABSTAINED)


class TestSampleAndTreatment(unittest.TestCase):
    def test_plasma(self):
        rec = make("Plasma proteomics of breast cancer patients")
        self.assertIn("plasma", get(rec, "sample_type").value)

    def test_pre_post(self):
        rec = make("Urinary EVs pre- and post-surgery in breast cancer patients")
        a = get(rec, "treatment_context")
        self.assertEqual(a.status, AssertionStatus.ASSERTED)
        self.assertIn("pre/post", a.value)


class TestProvenanceInvariant(unittest.TestCase):
    def test_every_asserted_claim_has_evidence(self):
        """Brief §12: a confident answer without provenance is a defect."""
        rec = make("ER+ luminal A breast cancer plasma study in patients, "
                   "pre- and post- treatment with tamoxifen")
        for a in rec.assertions:
            if a.status == AssertionStatus.ASSERTED:
                self.assertTrue(a.evidence_text,
                                f"{a.field} asserted without evidence_text")


class TestEndToEnd(unittest.TestCase):
    """Integration: seed DB -> search -> answer (uses a temp database)."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmp = tempfile.mkdtemp()
        os.environ["PXENRICH_DB"] = os.path.join(cls.tmp, "test.db")
        # reload db module default
        from importlib import reload
        from pxenrich import db as dbmod
        reload(dbmod)
        from pxenrich.ingest.run_ingest import ingest_seed
        cls.dbmod = dbmod
        conn = dbmod.connect()
        ingest_seed(conn)
        conn.close()

    @classmethod
    def tearDownClass(cls):
        os.environ.pop("PXENRICH_DB", None)
        from importlib import reload
        from pxenrich import db as dbmod
        reload(dbmod)

    def test_search_and_answer(self):
        from pxenrich.answer import compose_answer
        from pxenrich.search import search
        conn = self.dbmod.connect()
        r = search(conn, "Has HER2-low breast cancer been studied using proteomics?")
        self.assertGreater(r["total_matches"], 0)
        a = compose_answer(r["question"], r, "plain")
        self.assertEqual(a["status"], "ok")
        self.assertTrue(a["sources"], "answers must carry sources")
        self.assertIn("notice", a)
        conn.close()

    def test_empty_question_abstains(self):
        from pxenrich.answer import compose_answer
        from pxenrich.search import search
        conn = self.dbmod.connect()
        r = search(conn, "zebrafish kidney transcriptomics llama")
        a = compose_answer(r["question"], r, "plain")
        if not r["records"]:
            self.assertEqual(a["status"], "insufficient_evidence")
        conn.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
