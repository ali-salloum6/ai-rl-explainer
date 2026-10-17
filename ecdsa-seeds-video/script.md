# It's Just Timestamps: narration script

Syntax:
- `## Scene: Name` starts a scene (one Manim scene class per heading).
- `[id]` starts a narration segment. Each segment becomes one TTS clip.
- `{mark}` is a sync point placed just BEFORE the words it belongs to. It is never
  spoken; scenes call `v.wait_until("mark")` to time a visual beat.
- `[[display|spoken]]` shows `display` in subtitles and sends `spoken` to the TTS.
- Lines starting with `%` are director's notes and are ignored.

Sources: anthropic.com/research/ecdsa-curve-origins (Oct 16, 2026),
words.filippo.io/seeds-solved, Koblitz & Menezes "A Riddle Wrapped in an Enigma" (2015).

## Scene: ColdOpen

[c1] {num}This number has been quietly protecting the internet {years}for more than twenty-five years.

[c2] It's part of the definition of {p256}[[P-256|P-two-fifty-six]], one of the most widely used elliptic curves on Earth. It's behind {lock}the padlock in your browser, {key}the passkeys replacing your passwords, and {chip}the secure chip in your phone.

[c3] And yet, for all that time, {q}nobody could say where it came from. {crypto}Not the cryptographers who studied it. Apparently, {nobody}not even the people who made it.

[c4] Some suspected {door}it hid a backdoor. Two leading cryptographers wrote about the controversy in a paper titled {riddle}"A Riddle Wrapped in an Enigma." And {bounty}a bounty of nearly thirty-seven thousand dollars sat {unclaimed}unclaimed for three years.

[c5] Then, on {date}October sixteenth, 2026, {anth}Anthropic announced that {claude}Claude had solved the mystery, {fast}in under half an hour.

[c6] {answer}The answer fits in three words: {pause}"It's just timestamps."

[c7] To see why that answer is so satisfying, and how an AI found it, we'll build up from scratch: {r1}digital signatures, {r2}elliptic curves, {r3}the ECDSA algorithm, and then {r4}the detective story itself.

## Scene: Signatures

[s1] Every time you open a website, your browser has to answer one question: am I really talking to {bank}my bank, or to {eve}an impostor in the middle?

[s2] On paper, we'd use {sig}a signature. But online, {copyable}anything can be copied perfectly. A signature that's the same on every document is worthless: {copy}copy it once, and you can forge it forever.

[s3] A digital signature uses {keys}two keys. {priv}A private key, which only you hold, {sign}makes a signature that depends on every bit of the message. {pub}A public key, which anyone can have, {verify}lets the whole world check that signature, but {cant}can't make one.

[s4] {edit}Change a single character, and {fail}the signature no longer checks out.

[s5] So we need {oneway}a mathematical one-way street: easy to do, practically impossible to undo. {ecdsa}ECDSA, the Elliptic Curve Digital Signature Algorithm, builds one from two ingredients: {clockword}clock arithmetic, and {curveword}elliptic curves.

## Scene: ClockArithmetic

[k1] You already know clock arithmetic. If it's {nine}nine o'clock and you {move}wait five hours, it's {two}two o'clock, not fourteen. {wrap}Numbers wrap around.

[k2] Mathematicians write it like this: {eq}nine plus five equals two, mod twelve. "Mod" just means: {rem}divide by twelve, and keep the remainder.

[k3] Cryptography does the same with {prime}a prime instead of twelve. Take {p}one hundred and one, and look at {pow}powers of three: three, nine, twenty-seven, eighty-one... then {wrap}two hundred forty-three wraps around to forty-one.

[k4] Keep going, and {plot}plot the results. {random}They jump around as if they were random. There's no pattern to follow.

[k5] {fwd}Going forward is easy: even with numbers hundreds of digits long, a computer gets three to the power k almost instantly. {bwd}Going backward, from the answer to k, is called {dlp}the discrete logarithm problem. For big, well-chosen numbers, {hard}nobody knows a fast way to do it.

[k6] That's {street}our one-way street. Elliptic curves make it {harder}even harder to reverse. So let's meet them.

## Scene: EllipticCurves

[e1] An elliptic curve is the set of points satisfying {eq}an equation like this: y squared equals x cubed, plus a x, plus b. {shape}Nothing to do with ellipses. {draw}Drawn over ordinary numbers, it looks like this.

[e2] Here's the trick that makes it useful. Take {pq}two points on the curve, P and Q. {line}Draw the line through them. It always hits the curve {third}at exactly one more point. {reflect}Reflect that point across the horizontal axis, and {sum}call the result P plus Q.

[e3] To add a point to itself, use {tangent}the tangent line instead. That gives {twoP}P plus P, or two P.

[e4] This operation really does behave like addition: {props}there's a zero, every point has a negative, and order doesn't matter. So we can keep going: {p3}three P, {p4}four P, and {leap}the points leap around the curve.

[e5] And multiplying by a huge number is fast: {dbl}double, double, double, adding along the way. {fifty}A quadrillion times P takes about fifty doublings, not a quadrillion additions.

[e6] For cryptography, we do all of this in {mod}clock arithmetic, modulo a prime. {cloud}The smooth curve dissolves into a cloud of points. But {same}the same formulas still work.

[e7] Now take a point everyone agrees on: {G}the base point, G. Pick {d}a secret number d, and compute {Q}Q equals d times G. Even when d has {digits}nearly eighty digits, that takes {steps}just a few hundred steps.

[e8] {ecdlp}Going back, from Q to d, is the elliptic curve discrete logarithm problem. On [[P-256|P-two-fifty-six]], {twoto}the best known attack needs about two to the one hundred twenty-eight steps. {years}A billion computers, each doing a billion steps per second, would need around ten trillion years.

[e9] {priv}The secret d is your private key. {pub}Q is your public key. And {params}the curve itself, the prime p, the numbers a and b, the base point G, is a public standard that everyone shares. Remember that. {hide}It's where our mystery hides.

## Scene: ECDSA

[d1] So how do you sign? Say {msg}Alice wants to sign a message. First she {hash}hashes it with [[SHA-256|shah two fifty-six]], crushing it into a fixed-size fingerprint: {e}a number we'll call e.

[d2] Next, she picks {k}a fresh random number k, used only once. It's called {nonce}the nonce. She computes {R}the point R equals k times G, and keeps {r}its x-coordinate, r.

[d3] Then she computes {s}s equals k-inverse, times e plus r times d, modulo n, the number of points on the curve. {mask}Her private key d is mixed in here, masked by the random k. {sig}The signature is just two numbers: r and s.

[d4] To check it, Bob only needs {pubinfo}public information: the message, the signature, and Alice's public key Q. He computes {u1}u-one equals e over s, {u2}u-two equals r over s, and then {X}the point u-one times G, plus u-two times Q. If {check}its x-coordinate equals r, the signature is valid.

[d5] Why does that work? {sub}Replace Q with d times G. {collapse}Everything collapses to e plus r d, over s, times G. And because of how s was built, {kG}that's exactly k times G: the point R. {only}Only someone who knew d could have produced an s that lands there.

[d6] But notice {assume}the hidden assumption: the nonce k must be secret, unpredictable, and never reused. {reuse}If Alice signs two messages with the same k, anyone can {subtract}subtract the two equations, {solvek}solve for k, and then {solved}for her private key.

[d7] This isn't hypothetical. {ps3}In 2010, hackers recovered the private key Sony used to sign PlayStation 3 software, because {same}Sony used the same "random" number for every signature.

[d8] Even {bias}a small bias in k, a few predictable bits, can leak the key through {lattice}a powerful technique called lattice reduction. Remember that word: lattice. It's coming back.

[d9] So ECDSA rests on {pillars}three pillars: {p1}a hard math problem, {p2}good randomness, and one that almost nobody thinks about: {p3}the curve itself.

## Scene: CurveOrigins

[o1] {notsafe}Not every curve is safe. Some have hidden shortcuts: {weak}if a curve has exactly p points, for example, its discrete log falls apart almost instantly. Experts know these traps. But {secret}what if someone knew one that nobody else did?

[o2] If you knew {billion}a secret weakness shared by, say, one curve in a billion, you could {search}quietly test curves until you found a weak one, and {publish}publish it as the standard.

[o3] {nsa}In 1997 and 1998, the NSA generated a family of curves that became American standards: first in {ansi}a banking standard from ANSI, then in {fips}NIST's federal signature standard, which includes [[P-256|P-two-fifty-six]].

[o4] To prove nothing was up their sleeve, the curves were {vr}"verifiably random." The coefficient b wasn't chosen directly. Instead, {sha}a seed was fed into the [[SHA-1|shah one]] hash function, and {b}b was computed from the output.

[o5] {oneway}A hash can't be run backwards, so nobody could have picked b on purpose. But {catch}there's a catch. A hash stops you from choosing the output, not from {tries}trying a billion inputs. Verifiable randomness only works if {explain}the seed itself is explained. And {none}these seeds came with no explanation at all.

[o6] For years, that bothered only a few experts. Then, {snowden}in 2013, documents leaked by Edward Snowden indicated that the NSA had engineered a backdoor into another NIST standard: {dualec}a random number generator called [[Dual_EC_DRBG|Dual E-C D-R-B-G]]. It ran on {samecurve}the very same curve, [[P-256|P-two-fifty-six]], and its secret hid in {consts}two unexplained constants.

[o7] Overnight, {sus}every unexplained number from the NSA looked suspicious. The security expert Bruce Schneier wrote: {schneier}"I no longer trust the constants."

[o8] The seeds came from {jerry}NSA mathematician Jerry Solinas, so famous for fast primes that {prime}a whole family of them carries his name, including [[P-256|P-two-fifty-six]]'s. He recalled {phrase}hashing a humorous phrase, something like "Give Bob and Jerry a raise." But {lost}the details were forgotten, and the code was never found.

[o9] {hunt}People hashed endless variations of that phrase. Nothing matched. {rip}Solinas passed away in 2023. That same year, {bounty}cryptographer Filippo Valsorda launched a bounty: {amount}twelve thousand two hundred eighty-eight dollars, {triple}tripled to thirty-six thousand eight hundred sixty-four if donated to charity. {years}Three years went by. {unclaimed}Unclaimed.

## Scene: Investigation

[i1] {oct}October 2026. {nope}Several people at Anthropic had chased the passphrase theory, with no luck. Then one of them {ask}asked an internal research model: can you figure out how these seeds were generated? {nohint}No hint about the passphrase.

[i2] {angle}Claude took a different angle. Instead of guessing a phrase, it asked: {y1997}what software would have made these, in 1997? {cprog}Probably a C program, using {prng}the random number generator built into the C library. And those old generators are {fp}weak enough to leave fingerprints.

[i3] So {scan}Claude wrote a scanner. It {slide}slid along each seed one bit at a time, testing whether neighboring chunks could be consecutive outputs of a 1990s-vintage generator: {combos}thirty-four combinations of generators and output formats.

[i4] Then {notice}it noticed something. Write {words}the ten NIST seeds as 32-bit words. In {four}four of them, seeds for a sibling family called the binary curves, {zeros}the top bit of every single word is zero. By pure chance, {odds}that happens about once in fifty-eight hundred tries.

[i5] And one famous function leaves exactly that fingerprint: {name}[[lrand48|L-rand-forty-eight]].

[i6] It's {lcg}a classic Unix random number generator. Its entire memory is {state}one 48-bit number: the state. Each call {step}multiplies the state by a constant, adds eleven, and wraps around modulo two to the forty-eighth: {clock}clock arithmetic again. Then {out}it outputs only the top 31 bits. So {topbit}in a 32-bit word, the top bit is always zero.

[i7] So {hidden}each output hides just 17 bits of the state. Claude {brute}tried all one hundred thirty-one thousand possibilities for the first word, and {next}checked which one made the generator reproduce the next four words. {match}For all four seeds, one did.

## Scene: Lattice

[l1] {prime}The seeds of the prime curves, including [[P-256|P-two-fifty-six]], were harder. They came from the same generator, but {trim}each output was cut down to its top 8 bits. {show}Every byte of the seed shows 8 bits of a 48-bit state, and {hide}hides the other 40.

[l2] {toomany}That's a trillion possibilities per output, and Claude {which}didn't even know which 8 bits the seeds were showing. But there's a shortcut. {write}Each state is "known bits, plus a small unknown." {linear}Each step of the generator is a linear equation, modulo two to the forty-eighth. And {for}finding small solutions to linear equations is exactly what lattices are for.

[l3] {grid}A lattice is a perfectly regular grid of points, made by {basis}adding whole-number multiples of a few basis vectors. The same grid can be described by {bad}a terrible basis, long vectors pointing in almost the same direction, or by {good}a good one: short, and nearly perpendicular.

[l4] {lll}In 1982, Arjen Lenstra, Hendrik Lenstra and László Lovász published an algorithm, named L-L-L after them, that {reduce}takes a bad basis and efficiently turns it into a good one. {steps}Subtract, swap, repeat.

[l5] {encode}Encode the generator's equations as a lattice, run L-L-L, and {short}the hidden bits show up in one of its shortest vectors. {biased}It's the same tool that breaks ECDSA when nonces are biased. This time, {unlock}it unlocked a random number generator.

[l6] {windows}Running the solver at every bit position, {lit}ten seeds lit up at the same spot: the top 8 bits. {ten}Five NIST prime-curve seeds, and five more from the ANSI standard. {regen}Each recovered 48-bit state regenerated all 160 bits of its seed. {accident}That does not happen by accident.

## Scene: Rewind

[w1] One more trick. {back}This kind of generator runs backwards as easily as forwards: {inv}subtract eleven, then multiply by the inverse of the constant. So {rewind}Claude rewound each generator, step by step, looking for {born}the moment it was born.

[w2] When a C program initializes the generator with {srand}[[srand48|S-rand-forty-eight]], {c330e}the low 16 bits of the state are always set to the same constant: hexadecimal [[330E|three-three-zero-E]]. {top32}The top 32 bits are whatever number the programmer passed in.

[w3] {rewind}Rewind [[P-256|P-two-fifty-six]]'s generator about thirty-seven thousand steps, and {hit}you hit a state ending in [[330E|three-three-zero-E]]. {num}Its top 32 bits read 871,696,354. Read that as {unix}a Unix timestamp, seconds since January 1st, 1970, and you get {date}August 16th, 1997, at 1:52 and 34 seconds in the morning, UTC.

[w4] {clock}Someone had seeded the generator with the computer's clock. If that machine was on {east}the U.S. East Coast, they hit "run" on {friday}a Friday night, at 9:52 PM.

[w5] {luck}One plausible date could be luck. But {timeline}all ten prime-curve seeds rewind to timestamps between May 1997 and April 1998, {made}exactly when these curves were being made.

[w6] {code}The whole program, reconstructed, is just a few lines. {l_seed}Seed the generator with the time. {l_draw}Draw 20 bytes, keeping the top 8 bits of each output. {l_check}If that candidate seed gives a good curve, stop. {l_again}Otherwise, draw again. {l_1842}For [[P-256|P-two-fifty-six]], it took 1,842 tries.

[w7] {binary}The binary curves had a twist: their timestamps only make sense {halved}if the program halved the clock, which puts them on {apr}April 17th, 1998, two weeks after the run that produced [[P-224|P-two-twenty-four]].

[w8] {think}Claude's own reaction, preserved in its reasoning, was wonderfully skeptical: {quote}"This is astonishing: it solves the 25-year-old mystery. Hmm wait. {sim}Let me be skeptical: am I in some sort of simulated test environment?" Then {verify}it checked the math again. A 160-bit match from a 32-bit seed is no coincidence. {real}"It's real."

[w9] And {bonus}a bonus: for [[P-192|P-one-ninety-two]] and five related ANSI curves, Claude also traced {bp}the base points, which the seeds don't determine, to {freelip}the random number generator in FreeLIP, a big-number library by {arjen}Arjen Lenstra. Yes: {same}the first L in L-L-L.

## Scene: Meaning

[m1] {q}So, is ECDSA broken? {no}No. This isn't an attack. {items}Your passkeys, your HTTPS connections, the chip in your phone: {same}they're exactly as secure today as they were yesterday.

[m2] If anything, {good}it's good news. {fear}The fear was that the seeds had been cherry-picked from an enormous search, to plant a weakness. Instead, {repro}they came from a mundane process, a common generator seeded with the clock, that anyone can now reproduce.

[m3] {filippo}Filippo Valsorda, who ran the bounty, did the math. Even if the designers could have picked {anyts}any second of 1997 and 1998, and {cands}any of the first sixteen valid candidates, they'd have had {bits}barely thirty bits of freedom. {little}That's far too little to aim for a rare, secret class of weak curves.

[m4] {open}Some questions remain open. {skip}The [[P-256|P-two-fifty-six]] run skipped candidate 876, which would also have made a valid curve, and nobody knows why. {b163}One binary seed, [[B-163|B-one-sixty-three]], still fits nothing. And {bp}the base points of the bigger prime curves remain unexplained.

[m5] {isrg}The bounty, all thirty-six thousand eight hundred sixty-four dollars, is going to the Internet Security Research Group, {le}the nonprofit behind Let's Encrypt.

[m6] But {how}the bigger story is how it was solved. {phrase}For a quarter of a century, people hunted for a secret phrase. {better}Claude asked a better question: not {q1}"what was hashed?", but {q2}"what would 1990s software actually do?" Then it ran {thirty}the whole investigation in under thirty minutes.

[m7] {both}That cuts both ways. A model that recognizes a 1990s random number generator from a handful of bytes can {hides}find weak randomness wherever it hides: old standards, firmware, software we all rely on. {defenders}For defenders, that's a powerful tool, and a reminder of {lesson}cryptography's oldest lesson: {everything}for keys and nonces, randomness is everything. {clock}A clock is not a secret.

[m8] {end}As for the seeds: one of cryptography's most famous mysteries didn't end with a backdoor. {fin}It ended with a clock, ticking away on an August night in 1997.
