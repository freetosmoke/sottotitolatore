"""
Unit tests for SubStudio Project Library & Persistence Engine (FASE 1).
Tests project creation, listing, updating, media fallback resolution,
video-only vs subtitle project types, duplication, and API endpoints.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from project_manager import ProjectManager, resolve_media_location


class TestProjectLibrary(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="substudio_test_proj_")
        self.projects_dir = Path(self.temp_dir) / "projects"
        self.pm = ProjectManager(projects_dir=self.projects_dir)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_create_and_list_subtitles_project(self):
        """Verifica la creazione e il recupero di un progetto con sottotitoli."""
        payload = {
            "name": "Intervista Guglielmino",
            "type": "subtitles",
            "media": {
                "filename": "intervista.mp4",
                "stored_filename": "intervista_1.mp4",
                "server_path": "/fake/path/intervista_1.mp4",
                "url": "/media/intervista_1.mp4",
                "duration": 504.2,
            },
            "chunks": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.5,
                    "speaker": "Speaker 1",
                    "words": [{"word": "Benvenuti", "start": 0.0, "end": 1.0}],
                    "bold_indices": [0],
                }
            ],
            "settings": {"language": "it", "speaker_detection": True},
        }

        saved = self.pm.save_project(payload)
        self.assertTrue(saved["id"].startswith("proj_"))
        self.assertEqual(saved["name"], "Intervista Guglielmino")
        self.assertEqual(saved["type"], "subtitles")
        self.assertEqual(len(saved["chunks"]), 1)
        self.assertIn("created_at", saved)
        self.assertIn("updated_at", saved)

        # Verifica lista
        projs = self.pm.list_projects()
        self.assertEqual(len(projs), 1)
        self.assertEqual(projs[0]["id"], saved["id"])
        self.assertEqual(projs[0]["name"], "Intervista Guglielmino")
        self.assertEqual(projs[0]["chunks_count"], 1)

    def test_create_video_only_project(self):
        """Verifica che un progetto video-only sia persistito correttamente senza chunk."""
        payload = {
            "name": "Reel Instagram Senza Testo",
            "type": "video_only",
            "media": {
                "filename": "reel.mp4",
                "duration": 45.0,
            },
            "chunks": [],
        }

        saved = self.pm.save_project(payload)
        self.assertEqual(saved["type"], "video_only")
        self.assertEqual(saved["name"], "Reel Instagram Senza Testo")
        self.assertEqual(len(saved["chunks"]), 0)

        loaded = self.pm.get_project(saved["id"])
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["type"], "video_only")

    def test_video_clips_persistence(self):
        """Verifica che i tagli video (video_clips) siano salvati e ripristinati correttamente."""
        clips = [
            {"id": "c1", "start": 0.0, "end": 12.5, "duration": 12.5, "title": "Intro", "filter": "none", "speed": 1.0},
            {"id": "c2", "start": 12.5, "end": 28.0, "duration": 15.5, "title": "Parte 2", "filter": "bw_cinema", "speed": 1.25},
            {"id": "c3", "start": 28.0, "end": 45.0, "duration": 17.0, "title": "Finale", "filter": "vibrant", "speed": 1.0},
        ]
        payload = {
            "name": "Montaggio Tagli FASE 5",
            "type": "video_only",
            "media": {"filename": "clip.mp4", "duration": 45.0},
            "video_clips": clips,
        }
        saved = self.pm.save_project(payload)
        self.assertEqual(saved["type"], "video_only")
        self.assertEqual(len(saved["video_clips"]), 3)
        self.assertEqual(saved["video_clips"][1]["filter"], "bw_cinema")
        self.assertEqual(saved["video_clips"][1]["speed"], 1.25)

        # Verifica nella lista
        projs = self.pm.list_projects()
        found = next((p for p in projs if p["id"] == saved["id"]), None)
        self.assertIsNotNone(found)
        self.assertEqual(found["video_clips_count"], 3)

        # Verifica nel get_project
        loaded = self.pm.get_project(saved["id"])
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded["video_clips"]), 3)
        self.assertEqual(loaded["video_clips"][0]["title"], "Intro")
        self.assertEqual(loaded["video_clips"][2]["end"], 45.0)

    def test_media_location_resilience(self):
        """
        Verifica che se il percorso assoluto originale non esiste,
        la risoluzione media cerca tra le cartelle note e imposta missing=True se assente,
        senza perdere i dati del progetto.
        """
        # Creiamo un file temporaneo reale
        dummy_video = Path(self.temp_dir) / "real_video.mp4"
        dummy_video.write_bytes(b"\x00" * 1024)

        media = {
            "filename": "video.mp4",
            "stored_filename": "real_video.mp4",
            "server_path": "/percorso/inesistente/real_video.mp4",
        }

        # Simula risoluzione con file spostato
        res = resolve_media_location(media, "test_proj")
        # Deve segnalare missing se non trovato nei percorsi canonici
        self.assertTrue(res["missing"])

        # Ora passiamo il percorso reale
        media["server_path"] = str(dummy_video.resolve())
        res_found = resolve_media_location(media, "test_proj")
        self.assertFalse(res_found["missing"])
        self.assertEqual(res_found["server_path"], str(dummy_video.resolve()))
        self.assertEqual(res_found["size"], 1024)

    def test_update_project(self):
        """Verifica che un aggiornamento mantenga l'ID e aggiorni updated_at."""
        p = self.pm.save_project({"name": "Draft 1", "type": "subtitles"})
        pid = p["id"]
        created = p["created_at"]

        # Aggiorna
        p_updated = self.pm.save_project({
            "id": pid,
            "name": "Draft 1 Riveduto",
            "chunks": [{"id": 0, "start": 1.0, "end": 3.0, "words": []}],
        })

        self.assertEqual(p_updated["id"], pid)
        self.assertEqual(p_updated["name"], "Draft 1 Riveduto")
        self.assertEqual(p_updated["created_at"], created)
        self.assertEqual(len(p_updated["chunks"]), 1)

    def test_duplicate_and_delete_project(self):
        """Verifica la duplicazione e la cancellazione sicura di un progetto."""
        orig = self.pm.save_project({"name": "Master Project", "type": "subtitles"})
        pid = orig["id"]

        dup = self.pm.duplicate_project(pid)
        self.assertIsNotNone(dup)
        self.assertNotEqual(dup["id"], pid)
        self.assertEqual(dup["name"], "Master Project (Copia)")

        # Cancella originale
        del_res = self.pm.delete_project(pid)
        self.assertTrue(del_res)
        self.assertIsNone(self.pm.get_project(pid))

        # Il duplicato esiste ancora
        self.assertIsNotNone(self.pm.get_project(dup["id"]))


if __name__ == "__main__":
    unittest.main()
