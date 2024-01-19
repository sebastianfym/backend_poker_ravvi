from dataclasses import dataclass


@dataclass
class LevelInfo:
    level: int
    blind_small: int
    blind_big: int
    ante: int = 0


sng_standard = [LevelInfo(level=1, blind_small=10, blind_big=20, ante=0),
                LevelInfo(level=2, blind_small=15, blind_big=30, ante=0),
                LevelInfo(level=3, blind_small=20, blind_big=40, ante=0),
                LevelInfo(level=4, blind_small=30, blind_big=60, ante=0),
                LevelInfo(level=5, blind_small=40, blind_big=80, ante=0),
                LevelInfo(level=6, blind_small=50, blind_big=100, ante=0),
                LevelInfo(level=7, blind_small=75, blind_big=150, ante=0),
                LevelInfo(level=8, blind_small=100, blind_big=200, ante=0),
                LevelInfo(level=9, blind_small=125, blind_big=250, ante=0),
                LevelInfo(level=10, blind_small=150, blind_big=300, ante=0),
                LevelInfo(level=11, blind_small=200, blind_big=400, ante=0),
                LevelInfo(level=12, blind_small=250, blind_big=500, ante=0),
                LevelInfo(level=13, blind_small=300, blind_big=600, ante=0),
                LevelInfo(level=14, blind_small=400, blind_big=800, ante=0),
                LevelInfo(level=15, blind_small=500, blind_big=1000, ante=0),
                LevelInfo(level=16, blind_small=600, blind_big=1200, ante=0),
                LevelInfo(level=17, blind_small=700, blind_big=1400, ante=0),
                LevelInfo(level=18, blind_small=800, blind_big=1600, ante=0),
                LevelInfo(level=19, blind_small=1000, blind_big=2000, ante=0),
                LevelInfo(level=20, blind_small=1200, blind_big=2400, ante=0),
                LevelInfo(level=21, blind_small=1500, blind_big=3000, ante=0),
                LevelInfo(level=22, blind_small=2000, blind_big=4000, ante=0),
                LevelInfo(level=23, blind_small=2500, blind_big=5000, ante=0),
                LevelInfo(level=24, blind_small=3000, blind_big=6000, ante=0),
                LevelInfo(level=25, blind_small=4000, blind_big=8000, ante=0),
                LevelInfo(level=26, blind_small=5000, blind_big=10000, ante=0),
                LevelInfo(level=27, blind_small=6000, blind_big=12000, ante=0),
                LevelInfo(level=28, blind_small=8000, blind_big=16000, ante=0),
                LevelInfo(level=29, blind_small=10000, blind_big=20000, ante=0),
                LevelInfo(level=30, blind_small=15000, blind_big=30000, ante=0),
                LevelInfo(level=31, blind_small=20000, blind_big=40000, ante=0),
                LevelInfo(level=32, blind_small=25000, blind_big=50000, ante=0),
                LevelInfo(level=33, blind_small=30000, blind_big=60000, ante=0),
                LevelInfo(level=34, blind_small=40000, blind_big=80000, ante=0),
                LevelInfo(level=35, blind_small=50000, blind_big=100000, ante=0),
                LevelInfo(level=36, blind_small=80000, blind_big=160000, ante=0),
                LevelInfo(level=37, blind_small=100000, blind_big=200000, ante=0),
                LevelInfo(level=38, blind_small=150000, blind_big=300000, ante=0),
                LevelInfo(level=39, blind_small=200000, blind_big=400000, ante=0),
                LevelInfo(level=40, blind_small=250000, blind_big=500000, ante=0)]

sng_turbo = [LevelInfo(level=1, blind_small=25, blind_big=50, ante=0),
             LevelInfo(level=2, blind_small=50, blind_big=100, ante=0),
             LevelInfo(level=3, blind_small=100, blind_big=200, ante=0),
             LevelInfo(level=4, blind_small=150, blind_big=300, ante=0),
             LevelInfo(level=5, blind_small=200, blind_big=400, ante=0),
             LevelInfo(level=6, blind_small=250, blind_big=500, ante=0),
             LevelInfo(level=7, blind_small=300, blind_big=600, ante=0),
             LevelInfo(level=8, blind_small=400, blind_big=800, ante=0),
             LevelInfo(level=9, blind_small=500, blind_big=1000, ante=0),
             LevelInfo(level=10, blind_small=600, blind_big=1200, ante=0),
             LevelInfo(level=11, blind_small=800, blind_big=1600, ante=0),
             LevelInfo(level=12, blind_small=1000, blind_big=2000, ante=0),
             LevelInfo(level=13, blind_small=1500, blind_big=3000, ante=0),
             LevelInfo(level=14, blind_small=2000, blind_big=4000, ante=0),
             LevelInfo(level=15, blind_small=3000, blind_big=6000, ante=0),
             LevelInfo(level=16, blind_small=4000, blind_big=8000, ante=0),
             LevelInfo(level=17, blind_small=5000, blind_big=10000, ante=0),
             LevelInfo(level=18, blind_small=6000, blind_big=12000, ante=0),
             LevelInfo(level=19, blind_small=8000, blind_big=16000, ante=0),
             LevelInfo(level=20, blind_small=10000, blind_big=20000, ante=0),
             LevelInfo(level=21, blind_small=15000, blind_big=30000, ante=0),
             LevelInfo(level=22, blind_small=20000, blind_big=40000, ante=0),
             LevelInfo(level=23, blind_small=30000, blind_big=60000, ante=0),
             LevelInfo(level=24, blind_small=40000, blind_big=80000, ante=0),
             LevelInfo(level=25, blind_small=50000, blind_big=100000, ante=0),
             LevelInfo(level=26, blind_small=60000, blind_big=120000, ante=0),
             LevelInfo(level=27, blind_small=80000, blind_big=160000, ante=0),
             LevelInfo(level=28, blind_small=100000, blind_big=200000, ante=0),
             LevelInfo(level=29, blind_small=150000, blind_big=300000, ante=0),
             LevelInfo(level=30, blind_small=200000, blind_big=400000, ante=0),
             LevelInfo(level=31, blind_small=250000, blind_big=500000, ante=0),
             LevelInfo(level=32, blind_small=300000, blind_big=600000, ante=0),
             LevelInfo(level=33, blind_small=400000, blind_big=800000, ante=0),
             LevelInfo(level=34, blind_small=500000, blind_big=1000000, ante=0),
             LevelInfo(level=35, blind_small=1000000, blind_big=2000000, ante=0),
             LevelInfo(level=36, blind_small=2000000, blind_big=4000000, ante=0)]

mtt_standard = [LevelInfo(level=1, blind_small=10, blind_big=20, ante=0),
                LevelInfo(level=2, blind_small=15, blind_big=30, ante=0),
                LevelInfo(level=3, blind_small=20, blind_big=40, ante=0),
                LevelInfo(level=4, blind_small=30, blind_big=60, ante=5),
                LevelInfo(level=5, blind_small=40, blind_big=80, ante=8),
                LevelInfo(level=6, blind_small=50, blind_big=100, ante=10),
                LevelInfo(level=7, blind_small=75, blind_big=150, ante=15),
                LevelInfo(level=8, blind_small=100, blind_big=200, ante=20),
                LevelInfo(level=9, blind_small=125, blind_big=250, ante=25),
                LevelInfo(level=10, blind_small=150, blind_big=300, ante=30),
                LevelInfo(level=11, blind_small=200, blind_big=400, ante=40),
                LevelInfo(level=12, blind_small=250, blind_big=500, ante=50),
                LevelInfo(level=13, blind_small=300, blind_big=600, ante=60),
                LevelInfo(level=14, blind_small=400, blind_big=800, ante=80),
                LevelInfo(level=15, blind_small=500, blind_big=1000, ante=100),
                LevelInfo(level=16, blind_small=600, blind_big=1200, ante=120),
                LevelInfo(level=17, blind_small=700, blind_big=1400, ante=140),
                LevelInfo(level=18, blind_small=800, blind_big=1600, ante=160),
                LevelInfo(level=19, blind_small=1000, blind_big=2000, ante=200),
                LevelInfo(level=20, blind_small=1200, blind_big=2400, ante=250),
                LevelInfo(level=21, blind_small=1500, blind_big=3000, ante=300),
                LevelInfo(level=22, blind_small=1800, blind_big=3600, ante=350),
                LevelInfo(level=23, blind_small=2000, blind_big=4000, ante=400),
                LevelInfo(level=24, blind_small=2500, blind_big=5000, ante=500),
                LevelInfo(level=25, blind_small=3000, blind_big=6000, ante=600),
                LevelInfo(level=26, blind_small=3500, blind_big=7000, ante=700),
                LevelInfo(level=27, blind_small=4000, blind_big=8000, ante=800),
                LevelInfo(level=28, blind_small=5000, blind_big=10000, ante=1000),
                LevelInfo(level=29, blind_small=6000, blind_big=12000, ante=1200),
                LevelInfo(level=30, blind_small=8000, blind_big=16000, ante=1600),
                LevelInfo(level=31, blind_small=10000, blind_big=20000, ante=2000),
                LevelInfo(level=32, blind_small=12000, blind_big=24000, ante=2500),
                LevelInfo(level=33, blind_small=15000, blind_big=30000, ante=3000),
                LevelInfo(level=34, blind_small=20000, blind_big=40000, ante=4000),
                LevelInfo(level=35, blind_small=25000, blind_big=50000, ante=5000),
                LevelInfo(level=36, blind_small=30000, blind_big=60000, ante=6000),
                LevelInfo(level=37, blind_small=40000, blind_big=80000, ante=8000),
                LevelInfo(level=38, blind_small=50000, blind_big=100000, ante=10000),
                LevelInfo(level=39, blind_small=60000, blind_big=120000, ante=10000),
                LevelInfo(level=40, blind_small=80000, blind_big=160000, ante=15000),
                LevelInfo(level=41, blind_small=100000, blind_big=200000, ante=20000),
                LevelInfo(level=42, blind_small=120000, blind_big=240000, ante=25000),
                LevelInfo(level=43, blind_small=150000, blind_big=300000, ante=30000),
                LevelInfo(level=44, blind_small=200000, blind_big=400000, ante=40000),
                LevelInfo(level=45, blind_small=250000, blind_big=500000, ante=50000),
                LevelInfo(level=46, blind_small=300000, blind_big=600000, ante=60000),
                LevelInfo(level=47, blind_small=400000, blind_big=800000, ante=80000),
                LevelInfo(level=48, blind_small=500000, blind_big=1000000, ante=100000),
                LevelInfo(level=49, blind_small=600000, blind_big=1200000, ante=120000),
                LevelInfo(level=50, blind_small=800000, blind_big=1600000, ante=160000),
                LevelInfo(level=51, blind_small=1000000, blind_big=2000000, ante=200000),
                LevelInfo(level=52, blind_small=1500000, blind_big=3000000, ante=300000),
                LevelInfo(level=53, blind_small=2000000, blind_big=4000000, ante=400000),
                LevelInfo(level=54, blind_small=2500000, blind_big=5000000, ante=500000),
                LevelInfo(level=55, blind_small=3000000, blind_big=6000000, ante=600000),
                LevelInfo(level=56, blind_small=4000000, blind_big=8000000, ante=800000),
                LevelInfo(level=57, blind_small=5000000, blind_big=10000000, ante=1000000),
                LevelInfo(level=58, blind_small=6000000, blind_big=12000000, ante=1500000),
                LevelInfo(level=59, blind_small=8000000, blind_big=16000000, ante=1500000),
                LevelInfo(level=60, blind_small=10000000, blind_big=20000000, ante=2000000),
                LevelInfo(level=61, blind_small=15000000, blind_big=30000000, ante=3000000),
                LevelInfo(level=62, blind_small=20000000, blind_big=40000000, ante=4000000),
                LevelInfo(level=63, blind_small=25000000, blind_big=50000000, ante=5000000),
                LevelInfo(level=64, blind_small=30000000, blind_big=60000000, ante=6000000),
                LevelInfo(level=65, blind_small=40000000, blind_big=80000000, ante=8000000),
                LevelInfo(level=66, blind_small=50000000, blind_big=100000000, ante=10000000),
                LevelInfo(level=67, blind_small=60000000, blind_big=120000000, ante=10000000),
                LevelInfo(level=68, blind_small=80000000, blind_big=160000000, ante=15000000),
                LevelInfo(level=69, blind_small=100000000, blind_big=200000000, ante=20000000),
                LevelInfo(level=70, blind_small=150000000, blind_big=300000000, ante=30000000),
                LevelInfo(level=71, blind_small=200000000, blind_big=400000000, ante=40000000),
                LevelInfo(level=72, blind_small=250000000, blind_big=500000000, ante=50000000),
                LevelInfo(level=73, blind_small=300000000, blind_big=600000000, ante=60000000),
                LevelInfo(level=74, blind_small=400000000, blind_big=800000000, ante=80000000),
                LevelInfo(level=75, blind_small=500000000, blind_big=1000000000, ante=100000000),
                LevelInfo(level=76, blind_small=600000000, blind_big=1200000000, ante=100000000),
                LevelInfo(level=77, blind_small=800000000, blind_big=1600000000, ante=150000000),
                LevelInfo(level=78, blind_small=1000000000, blind_big=2000000000, ante=200000000),
                LevelInfo(level=79, blind_small=1500000000, blind_big=3000000000, ante=300000000),
                LevelInfo(level=80, blind_small=2000000000, blind_big=4000000000, ante=400000000)]


mtt_turbo = [LevelInfo(level=1, blind_small=25, blind_big=50, ante=0),
             LevelInfo(level=2, blind_small=50, blind_big=100, ante=0),
             LevelInfo(level=3, blind_small=100, blind_big=200, ante=25),
             LevelInfo(level=4, blind_small=150, blind_big=300, ante=50),
             LevelInfo(level=5, blind_small=200, blind_big=400, ante=50),
             LevelInfo(level=6, blind_small=250, blind_big=500, ante=75),
             LevelInfo(level=7, blind_small=300, blind_big=600, ante=75),
             LevelInfo(level=8, blind_small=400, blind_big=800, ante=100),
             LevelInfo(level=9, blind_small=500, blind_big=1000, ante=100),
             LevelInfo(level=10, blind_small=600, blind_big=1200, ante=200),
             LevelInfo(level=11, blind_small=800, blind_big=1600, ante=200),
             LevelInfo(level=12, blind_small=1000, blind_big=2000, ante=300),
             LevelInfo(level=13, blind_small=1200, blind_big=2400, ante=300),
             LevelInfo(level=14, blind_small=1500, blind_big=3000, ante=400),
             LevelInfo(level=15, blind_small=2000, blind_big=4000, ante=500),
             LevelInfo(level=16, blind_small=2500, blind_big=5000, ante=800),
             LevelInfo(level=17, blind_small=3000, blind_big=6000, ante=1000),
             LevelInfo(level=18, blind_small=4000, blind_big=8000, ante=1000),
             LevelInfo(level=19, blind_small=5000, blind_big=10000, ante=1500),
             LevelInfo(level=20, blind_small=6000, blind_big=12000, ante=1500),
             LevelInfo(level=21, blind_small=8000, blind_big=16000, ante=2000),
             LevelInfo(level=22, blind_small=10000, blind_big=20000, ante=3000),
             LevelInfo(level=23, blind_small=12000, blind_big=24000, ante=3000),
             LevelInfo(level=24, blind_small=15000, blind_big=30000, ante=4000),
             LevelInfo(level=25, blind_small=20000, blind_big=40000, ante=5000),
             LevelInfo(level=26, blind_small=25000, blind_big=50000, ante=6000),
             LevelInfo(level=27, blind_small=30000, blind_big=60000, ante=8000),
             LevelInfo(level=28, blind_small=40000, blind_big=80000, ante=10000),
             LevelInfo(level=29, blind_small=50000, blind_big=100000, ante=15000),
             LevelInfo(level=30, blind_small=60000, blind_big=120000, ante=15000),
             LevelInfo(level=31, blind_small=80000, blind_big=160000, ante=20000),
             LevelInfo(level=32, blind_small=100000, blind_big=200000, ante=30000),
             LevelInfo(level=33, blind_small=120000, blind_big=240000, ante=30000),
             LevelInfo(level=34, blind_small=150000, blind_big=300000, ante=50000),
             LevelInfo(level=35, blind_small=200000, blind_big=400000, ante=50000),
             LevelInfo(level=36, blind_small=250000, blind_big=500000, ante=75000),
             LevelInfo(level=37, blind_small=300000, blind_big=600000, ante=100000),
             LevelInfo(level=38, blind_small=400000, blind_big=800000, ante=100000),
             LevelInfo(level=39, blind_small=500000, blind_big=1000000, ante=150000),
             LevelInfo(level=40, blind_small=600000, blind_big=1200000, ante=200000),
             LevelInfo(level=41, blind_small=800000, blind_big=1600000, ante=250000),
             LevelInfo(level=42, blind_small=1000000, blind_big=2000000, ante=300000),
             LevelInfo(level=43, blind_small=1500000, blind_big=3000000, ante=400000),
             LevelInfo(level=44, blind_small=2000000, blind_big=4000000, ante=500000),
             LevelInfo(level=45, blind_small=2500000, blind_big=5000000, ante=800000),
             LevelInfo(level=46, blind_small=3000000, blind_big=6000000, ante=1000000),
             LevelInfo(level=47, blind_small=4000000, blind_big=8000000, ante=1000000),
             LevelInfo(level=48, blind_small=5000000, blind_big=10000000, ante=1500000),
             LevelInfo(level=49, blind_small=6000000, blind_big=12000000, ante=1500000),
             LevelInfo(level=50, blind_small=8000000, blind_big=16000000, ante=2000000),
             LevelInfo(level=51, blind_small=10000000, blind_big=20000000, ante=3000000),
             LevelInfo(level=52, blind_small=15000000, blind_big=30000000, ante=3000000),
             LevelInfo(level=53, blind_small=20000000, blind_big=40000000, ante=5000000),
             LevelInfo(level=54, blind_small=30000000, blind_big=60000000, ante=10000000),
             LevelInfo(level=55, blind_small=40000000, blind_big=80000000, ante=10000000),
             LevelInfo(level=56, blind_small=50000000, blind_big=100000000, ante=15000000),
             LevelInfo(level=57, blind_small=60000000, blind_big=120000000, ante=15000000),
             LevelInfo(level=58, blind_small=80000000, blind_big=160000000, ante=20000000),
             LevelInfo(level=59, blind_small=100000000, blind_big=200000000, ante=30000000),
             LevelInfo(level=60, blind_small=150000000, blind_big=300000000, ante=30000000),
             LevelInfo(level=61, blind_small=200000000, blind_big=400000000, ante=50000000),
             LevelInfo(level=62, blind_small=300000000, blind_big=600000000, ante=100000000),
             LevelInfo(level=63, blind_small=400000000, blind_big=800000000, ante=100000000),
             LevelInfo(level=64, blind_small=500000000, blind_big=1000000000, ante=150000000),
             LevelInfo(level=65, blind_small=600000000, blind_big=1200000000, ante=150000000),
             LevelInfo(level=66, blind_small=800000000, blind_big=1600000000, ante=200000000),
             LevelInfo(level=67, blind_small=1000000000, blind_big=2000000000, ante=300000000),
             LevelInfo(level=68, blind_small=1500000000, blind_big=3000000000, ante=300000000),
             LevelInfo(level=69, blind_small=2000000000, blind_big=4000000000, ante=500000000),
             LevelInfo(level=70, blind_small=3000000000, blind_big=6000000000, ante=1000000000)]


mtt_hyperturbo = [LevelInfo(level=1, blind_small=50, blind_big=100, ante=0),
                   LevelInfo(level=2, blind_small=100, blind_big=200, ante=0),
                   LevelInfo(level=3, blind_small=150, blind_big=300, ante=50),
                   LevelInfo(level=4, blind_small=200, blind_big=400, ante=50),
                   LevelInfo(level=5, blind_small=300, blind_big=600, ante=75),
                   LevelInfo(level=6, blind_small=400, blind_big=800, ante=100),
                   LevelInfo(level=7, blind_small=500, blind_big=1000, ante=150),
                   LevelInfo(level=8, blind_small=600, blind_big=1200, ante=200),
                   LevelInfo(level=9, blind_small=800, blind_big=1600, ante=200),
                   LevelInfo(level=10, blind_small=1000, blind_big=2000, ante=300),
                   LevelInfo(level=11, blind_small=1500, blind_big=3000, ante=400),
                   LevelInfo(level=12, blind_small=2000, blind_big=4000, ante=500),
                   LevelInfo(level=13, blind_small=3000, blind_big=6000, ante=800),
                   LevelInfo(level=14, blind_small=4000, blind_big=8000, ante=1000),
                   LevelInfo(level=15, blind_small=5000, blind_big=10000, ante=1500),
                   LevelInfo(level=16, blind_small=6000, blind_big=12000, ante=1500),
                   LevelInfo(level=17, blind_small=8000, blind_big=16000, ante=2000),
                   LevelInfo(level=18, blind_small=10000, blind_big=20000, ante=3000),
                   LevelInfo(level=19, blind_small=15000, blind_big=30000, ante=4000),
                   LevelInfo(level=20, blind_small=20000, blind_big=40000, ante=5000),
                   LevelInfo(level=21, blind_small=30000, blind_big=60000, ante=8000),
                   LevelInfo(level=22, blind_small=40000, blind_big=80000, ante=10000),
                   LevelInfo(level=23, blind_small=50000, blind_big=100000, ante=15000),
                   LevelInfo(level=24, blind_small=60000, blind_big=120000, ante=15000),
                   LevelInfo(level=25, blind_small=80000, blind_big=160000, ante=20000),
                   LevelInfo(level=26, blind_small=100000, blind_big=200000, ante=30000),
                   LevelInfo(level=27, blind_small=150000, blind_big=300000, ante=40000),
                   LevelInfo(level=28, blind_small=200000, blind_big=400000, ante=50000),
                   LevelInfo(level=29, blind_small=300000, blind_big=600000, ante=80000),
                   LevelInfo(level=30, blind_small=400000, blind_big=800000, ante=100000),
                   LevelInfo(level=31, blind_small=500000, blind_big=1000000, ante=150000),
                   LevelInfo(level=32, blind_small=600000, blind_big=1200000, ante=175000),
                   LevelInfo(level=33, blind_small=800000, blind_big=1600000, ante=200000),
                   LevelInfo(level=34, blind_small=1000000, blind_big=2000000, ante=300000),
                   LevelInfo(level=35, blind_small=1500000, blind_big=3000000, ante=400000),
                   LevelInfo(level=36, blind_small=2000000, blind_big=4000000, ante=500000),
                   LevelInfo(level=37, blind_small=3000000, blind_big=6000000, ante=700000),
                   LevelInfo(level=38, blind_small=4000000, blind_big=8000000, ante=1000000),
                   LevelInfo(level=39, blind_small=5000000, blind_big=10000000, ante=1500000),
                   LevelInfo(level=40, blind_small=6000000, blind_big=12000000, ante=1750000),
                   LevelInfo(level=41, blind_small=8000000, blind_big=16000000, ante=2000000),
                   LevelInfo(level=42, blind_small=10000000, blind_big=20000000, ante=3000000),
                   LevelInfo(level=43, blind_small=15000000, blind_big=30000000, ante=4000000),
                   LevelInfo(level=44, blind_small=20000000, blind_big=40000000, ante=5000000),
                   LevelInfo(level=45, blind_small=30000000, blind_big=60000000, ante=7000000),
                   LevelInfo(level=46, blind_small=40000000, blind_big=80000000, ante=10000000),
                   LevelInfo(level=47, blind_small=50000000, blind_big=100000000, ante=15000000),
                   LevelInfo(level=48, blind_small=60000000, blind_big=120000000, ante=17500000),
                   LevelInfo(level=49, blind_small=80000000, blind_big=160000000, ante=20000000),
                   LevelInfo(level=50, blind_small=100000000, blind_big=200000000, ante=30000000),
                   LevelInfo(level=51, blind_small=150000000, blind_big=300000000, ante=40000000),
                   LevelInfo(level=52, blind_small=200000000, blind_big=400000000, ante=50000000),
                   LevelInfo(level=53, blind_small=300000000, blind_big=600000000, ante=70000000),
                   LevelInfo(level=54, blind_small=400000000, blind_big=800000000, ante=100000000),
                   LevelInfo(level=55, blind_small=500000000, blind_big=1000000000, ante=150000000),
                   LevelInfo(level=56, blind_small=600000000, blind_big=1200000000, ante=175000000),
                   LevelInfo(level=57, blind_small=800000000, blind_big=1600000000, ante=200000000),
                   LevelInfo(level=58, blind_small=1000000000, blind_big=2000000000, ante=300000000),
                   LevelInfo(level=59, blind_small=1500000000, blind_big=3000000000, ante=400000000),
                   LevelInfo(level=60, blind_small=2000000000, blind_big=4000000000, ante=500000000)]


levels_schedule = {
    'sng':
        {
            'standard': sng_standard,
            'turbo': sng_turbo
        },
    'mtt': {
        'standard': mtt_standard,
        'turbo': mtt_turbo,
        'hyperturbo': mtt_hyperturbo
    }
}

rewards_distribution = {
    "payment":
        [
            {"players": [1, 3], "position": {"first": 1.0, "second": 0.0, "third": 0.0}},
            {"players": [4, 6], "position": {"first": 0.7, "second": 0.3, "third": 0.0}},
            {"players": [7, 9], "position": {"first": 0.5, "second": 0.3, "third": 0.2}}
        ]
}