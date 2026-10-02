# Arabic narration — candidates (Syrian dialect, like videos 1 and 2)

One entry per spoken line, in order: its key in `config/narration.json`, the English line, then 2–3 Arabic
versions. **★ = the one I recommend.** Write your pick after **Decision:** (1, 2, 3, or your own wording);
`scripts/build_narration_ar.py` turns the decisions into `config/narration_ar.json`, which the recorder reads.

Spelling and dialect follow video 2's `docs/arabic_script.md` ("How it's written").

Entry format, shown indented so the parser skips it (it reads `### … `key``, numbered options and **Decision:** at the start of a line):

```
    ### `hook.1`  ·  then 0.4s pause

    EN: <English line>

    ★ 1) <Arabic option>
       2) <Arabic option>

    **Decision:**
```

## Words used

| English | Arabic | note |
|---|---|---|

---
