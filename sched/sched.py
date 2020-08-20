from typing import Any, Iterable, Mapping, Tuple

class scheduler():
    def __init__(self, timing: Iterable[Tuple[int, Any]]) -> None:
        period = self._find_period([x for x,v in timing])
        steps = [{i/k : v for i in range(1, int(period * k)+1)} for k, v in timing]
        self.timings = {x:[d[x] for d in steps if x in d] for x in dict.fromkeys(sorted([b for a in steps for b in a]))}

        self.total = 0.0
        self.t = 0.0
        self.dt = 0.0

    def next_timing(self):
        while 1:
            self.t %= max(self.timings)
            self.t += self.dt
            try:
                self.dt = min([x - self.t for x in self.timings if x > self.t])
            except ValueError:
                self.dt = min(self.timings)

            self.total += self.dt
            yield self.dt, self.timings.get(self.t, self.timings[max(self.timings)])

    def _factorize(self, val: int) -> Mapping[int, int]:
        factors = {}
        while val > 1:
            for i in range(2, val+1):
                if val % i == 0:
                    factors[i] = factors[i] + 1 if i in factors else 1
                    val //= i
                    break
        return factors

    def _lcm(self, vals: Iterable[int]) -> int:
        lcm = 1
        factors = [self._factorize(round(x)) for x in vals]
        lcm_factors = {k: max([d.get(k, 0) for d in factors]) for k in dict.fromkeys([y for x in factors for y in x.keys()]).keys()}
        [lcm := lcm * k ** v for k,v in lcm_factors.items()]
        return lcm

    def _gcd(self, vals: Iterable[int]) -> int:
        gcd = 1
        factors = [self._factorize(round(x)) for x in vals]
        gcd_factors = {k: min([d.get(k, 0) for d in factors]) for k in dict.fromkeys([y for x in factors for y in x.keys()]).keys()}
        [gcd := gcd * k ** v for k,v in gcd_factors.items()]
        return gcd

    def _find_period(self, vals: Iterable[int]) -> float:
        return 1/self._gcd(vals)

    def __iter__(self):
        return self.next_timing()

    def __next__(self):
        return self.next_timing()