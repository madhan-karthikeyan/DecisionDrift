from pathlib import Path

from decisiondrift.bootstrap.v3 import build_repository_model

model = build_repository_model(
    Path("/home/madhan/.gemini/antigravity/brain/d499cfce-622f-419d-bb97-4993742455f3/scratch/goRateLimiter")
)
for t in model.technologies:
    print(f"{t.name}: conf={t.confidence}, evidence={t.evidence}")
