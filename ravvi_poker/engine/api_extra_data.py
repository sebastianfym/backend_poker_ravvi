from dataclasses import dataclass

@dataclass
class LevelInfo:
    blind_small: int
    blind_big: int
    ante: int = 0

sng_standard = [
                [LevelInfo( 10, 20)],
                [2, [15, 30], 0], 
                [3, [20, 40], 0], 
                [4, [30, 60], 0], 
                [5, [40, 80], 0],
                [6, [50, 100], 0], [7, [75, 150], 0], [8, [100, 200], 0], [9, [125, 250], 0],
                [10, [150, 300], 0], [11, [200, 400], 0], [12, [250, 500], 0], [13, [300, 600], 0],
                [14, [400, 800], 0], [15, [500, 1000], 0], [16, [600, 1200], 0], [17, [700, 1400], 0],
                [18, [800, 1600], 0], [19, [1000, 2000], 0], [20, [1200, 2400], 0], [21, [1500, 3000], 0],
                [22, [2000, 4000], 0], [23, [2500, 5000], 0], [24, [3000, 6000], 0], [25, [4000, 8000], 0],
                [26, [5000, 10000], 0], [27, [6000, 12000], 0], [28, [8000, 16000], 0],
                [29, [10000, 20000], 0], [30, [15000, 30000], 0], [31, [20000, 40000], 0],
                [32, [25000, 50000], 0], [33, [30000, 60000], 0], [34, [40000, 80000], 0],
                [35, [50000, 100000], 0], [36, [80000, 160000], 0], [37, [100000, 200000], 0],
                [38, [150000, 300000], 0], [39, [200000, 400000], 0], [40, [250000, 500000], 0]
               ]

sng_turbo = [
                [1, [25, 50], 0], [2, [50, 100], 0], [3, [100, 200], 0], [4, [150, 300], 0],
                [5, [200, 400], 0], [6, [250, 500], 0], [7, [300, 600], 0], [8, [400, 800], 0],
                [9, [500, 1000], 0], [10, [600, 1200], 0], [11, [800, 1600], 0], [12, [1000, 2000], 0],
                [13, [1500, 3000], 0], [14, [2000, 4000], 0], [15, [3000, 6000], 0], [16, [4000, 8000], 0],
                [17, [5000, 10000], 0], [18, [6000, 12000], 0], [19, [8000, 16000], 0],
                [20, [10000, 20000], 0], [21, [15000, 30000], 0], [22, [20000, 40000], 0],
                [23, [30000, 60000], 0], [24, [40000, 80000], 0], [25, [50000, 100000], 0],
                [26, [60000, 120000], 0], [27, [80000, 160000], 0], [28, [100000, 200000], 0],
                [29, [150000, 300000], 0], [30, [200000, 400000], 0], [31, [250000, 500000], 0],
                [32, [300000, 600000], 0], [33, [400000, 800000], 0], [34, [500000, 1000000], 0],
                [35, [1000000, 2000000], 0], [36, [2000000, 4000000], 0]
            ]

mtt_standard = [
                    [1, [10, 20], 0], [2, [15, 30], 0], [3, [20, 40], 0], [4, [30, 60], 5], [5, [40, 80], 8],
                    [6, [50, 100], 10], [7, [75, 150], 15], [8, [100, 200], 20], [9, [125, 250], 25], [10, [150, 300], 30],
                    [11, [200, 400], 40], [12, [250, 500], 50], [13, [300, 600], 60], [14, [400, 800], 80],
                    [15, [500, 1000], 100], [16, [600, 1200], 120], [17, [700, 1400], 140], [18, [800, 1600], 160],
                    [19, [1000, 2000], 200], [20, [1200, 2400], 250], [21, [1500, 3000], 300], [22, [1800, 3600], 350],
                    [23, [2000, 4000], 400], [24, [2500, 5000], 500], [25, [3000, 6000], 600], [26, [3500, 7000], 700],
                    [27, [4000, 8000], 800], [28, [5000, 10000], 1000], [29, [6000, 12000], 1200],
                    [30, [8000, 16000], 1600], [31, [10000, 20000], 2000], [32, [12000, 24000], 2500],
                    [33, [15000, 30000], 3000], [34, [20000, 40000], 4000], [35, [25000, 50000], 5000],
                    [36, [30000, 60000], 6000], [37, [40000, 80000], 8000], [38, [50000, 100000], 10000],
                    [39, [60000, 120000], 10000], [40, [80000, 160000], 15000], [41, [100000, 200000], 20000],
                    [42, [120000, 240000], 25000], [43, [150000, 300000], 30000], [44, [200000, 400000], 40000],
                    [45, [250000, 500000], 50000], [46, [300000, 600000], 60000], [47, [400000, 800000], 80000],
                    [48, [500000, 1000000], 100000], [49, [600000, 1200000], 120000], [50, [800000, 1600000], 160000],
                    [51, [1000000, 2000000], 200000], [52, [1500000, 3000000], 300000], [53, [2000000, 4000000], 400000],
                    [54, [2500000, 5000000], 500000], [55, [3000000, 6000000], 600000], [56, [4000000, 8000000], 800000],
                    [57, [5000000, 10000000], 1000000], [58, [6000000, 12000000], 1500000],
                    [59, [8000000, 16000000], 1500000], [60, [10000000, 20000000], 2000000],
                    [61, [15000000, 30000000], 3000000], [62, [20000000, 40000000], 4000000],
                    [63, [25000000, 50000000], 5000000], [64, [30000000, 60000000], 6000000],
                    [65, [40000000, 80000000], 8000000], [66, [50000000, 100000000], 10000000],
                    [67, [60000000, 120000000], 10000000], [68, [80000000, 160000000], 15000000],
                    [69, [100000000, 200000000], 20000000], [70, [150000000, 300000000], 30000000],
                    [71, [200000000, 400000000], 40000000], [72, [250000000, 500000000], 50000000],
                    [73, [300000000, 600000000], 60000000], [74, [400000000, 800000000], 80000000],
                    [75, [500000000, 1000000000], 100000000], [76, [600000000, 1200000000], 100000000],
                    [77, [800000000, 1600000000], 150000000], [78, [1000000000, 2000000000], 200000000],
                    [79, [1500000000, 3000000000], 300000000], [80, [2000000000, 4000000000], 400000000]
               ]

mtt_turbo = [
                [1, [25, 50], 0], [2, [50, 100], 0], [3, [100, 200], 25], [4, [150, 300], 50], [5, [200, 400], 50],
                [6, [250, 500], 75], [7, [300, 600], 75], [8, [400, 800], 100], [9, [500, 1000], 100],
                [10, [600, 1200], 200], [11, [800, 1600], 200], [12, [1000, 2000], 300], [13, [1200, 2400], 300],
                [14, [1500, 3000], 400], [15, [2000, 4000], 500], [16, [2500, 5000], 800], [17, [3000, 6000], 1000],
                [18, [4000, 8000], 1000], [19, [5000, 10000], 1500], [20, [6000, 12000], 1500], [21, [8000, 16000], 2000],
                [22, [10000, 20000], 3000], [23, [12000, 24000], 3000], [24, [15000, 30000], 4000],
                [25, [20000, 40000], 5000], [26, [25000, 50000], 6000], [27, [30000, 60000], 8000],
                [28, [40000, 80000], 10000], [29, [50000, 100000], 15000], [30, [60000, 120000], 15000],
                [31, [80000, 160000], 20000], [32, [100000, 200000], 30000], [33, [120000, 240000], 30000],
                [34, [150000, 300000], 50000], [35, [200000, 400000], 50000], [36, [250000, 500000], 75000],
                [37, [300000, 600000], 100000], [38, [400000, 800000], 100000], [39, [500000, 1000000], 150000],
                [40, [600000, 1200000], 200000], [41, [800000, 1600000], 250000], [42, [1000000, 2000000], 300000],
                [43, [1500000, 3000000], 400000], [44, [2000000, 4000000], 500000], [45, [2500000, 5000000], 800000],
                [46, [3000000, 6000000], 1000000], [47, [4000000, 8000000], 1000000], [48, [5000000, 10000000], 1500000],
                [49, [6000000, 12000000], 1500000], [50, [8000000, 16000000], 2000000],
                [51, [10000000, 20000000], 3000000], [52, [15000000, 30000000], 3000000],
                [53, [20000000, 40000000], 5000000], [54, [30000000, 60000000], 10000000],
                [55, [40000000, 80000000], 10000000], [56, [50000000, 100000000], 15000000],
                [57, [60000000, 120000000], 15000000], [58, [80000000, 160000000], 20000000],
                [59, [100000000, 200000000], 30000000], [60, [150000000, 300000000], 30000000],
                [61, [200000000, 400000000], 50000000], [62, [300000000, 600000000], 100000000],
                [63, [400000000, 800000000], 100000000], [64, [500000000, 1000000000], 150000000],
                [65, [600000000, 1200000000], 150000000], [66, [800000000, 1600000000], 200000000],
                [67, [1000000000, 2000000000], 300000000], [68, [1500000000, 3000000000], 300000000],
                [69, [2000000000, 4000000000], 500000000], [70, [3000000000, 6000000000], 1000000000]
            ]

mtt_hyper_turbo= [
                    [1, [50, 100], 0], [2, [100, 200], 0], [3, [150, 300], 50], [4, [200, 400], 50],
                    [5, [300, 600], 75], [6, [400, 800], 100], [7, [500, 1000], 150], [8, [600, 1200], 200],
                    [9, [800, 1600], 200], [10, [1000, 2000], 300], [11, [1500, 3000], 400], [12, [2000, 4000], 500],
                    [13, [3000, 6000], 800], [14, [4000, 8000], 1000], [15, [5000, 10000], 1500],
                    [16, [6000, 12000], 1500], [17, [8000, 16000], 2000], [18, [10000, 20000], 3000],
                    [19, [15000, 30000], 4000], [20, [20000, 40000], 5000], [21, [30000, 60000], 8000],
                    [22, [40000, 80000], 10000], [23, [50000, 100000], 15000], [24, [60000, 120000], 15000],
                    [25, [80000, 160000], 20000], [26, [100000, 200000], 30000], [27, [150000, 300000], 40000],
                    [28, [200000, 400000], 50000], [29, [300000, 600000], 80000], [30, [400000, 800000], 100000],
                    [31, [500000, 1000000], 150000], [32, [600000, 1200000], 175000], [33, [800000, 1600000], 200000],
                    [34, [1000000, 2000000], 300000], [35, [1500000, 3000000], 400000],
                    [36, [2000000, 4000000], 500000], [37, [3000000, 6000000], 700000],
                    [38, [4000000, 8000000], 1000000], [39, [5000000, 10000000], 1500000],
                    [40, [6000000, 12000000], 1750000], [41, [8000000, 16000000], 2000000],
                    [42, [10000000, 20000000], 3000000], [43, [15000000, 30000000], 4000000],
                    [44, [20000000, 40000000], 5000000], [45, [30000000, 60000000], 7000000],
                    [46, [40000000, 80000000], 10000000], [47, [50000000, 100000000], 15000000],
                    [48, [60000000, 120000000], 17500000], [49, [80000000, 160000000], 20000000],
                    [50, [100000000, 200000000], 30000000], [51, [150000000, 300000000], 40000000],
                    [52, [200000000, 400000000], 50000000], [53, [300000000, 600000000], 70000000],
                    [54, [400000000, 800000000], 100000000], [55, [500000000, 1000000000], 150000000],
                    [56, [600000000, 1200000000], 175000000], [57, [800000000, 1600000000], 200000000],
                    [58, [1000000000, 2000000000], 300000000], [59, [1500000000, 3000000000], 400000000],
                    [60, [2000000000, 4000000000], 500000000]
                 ]

blinds_information = {
    'sng':
           {'standard': [
               [1, [10, 20], 0], [2, [15, 30], 0], [3, [20, 40], 0], [4, [30, 60], 0], [5, [40, 80], 0],
               [6, [50, 100], 0], [7, [75, 150], 0], [8, [100, 200], 0], [9, [125, 250], 0],
               [10, [150, 300], 0], [11, [200, 400], 0], [12, [250, 500], 0], [13, [300, 600], 0],
               [14, [400, 800], 0], [15, [500, 1000], 0], [16, [600, 1200], 0], [17, [700, 1400], 0],
               [18, [800, 1600], 0], [19, [1000, 2000], 0], [20, [1200, 2400], 0], [21, [1500, 3000], 0],
               [22, [2000, 4000], 0], [23, [2500, 5000], 0], [24, [3000, 6000], 0], [25, [4000, 8000], 0],
               [26, [5000, 10000], 0], [27, [6000, 12000], 0], [28, [8000, 16000], 0],
               [29, [10000, 20000], 0], [30, [15000, 30000], 0], [31, [20000, 40000], 0],
               [32, [25000, 50000], 0], [33, [30000, 60000], 0], [34, [40000, 80000], 0],
               [35, [50000, 100000], 0], [36, [80000, 160000], 0], [37, [100000, 200000], 0],
               [38, [150000, 300000], 0], [39, [200000, 400000], 0], [40, [250000, 500000], 0]
           ],
               'turbo': [
                    [1, [25, 50], 0], [2, [50, 100], 0], [3, [100, 200], 0], [4, [150, 300], 0],
                        [5, [200, 400], 0], [6, [250, 500], 0], [7, [300, 600], 0], [8, [400, 800], 0],
                        [9, [500, 1000], 0], [10, [600, 1200], 0], [11, [800, 1600], 0], [12, [1000, 2000], 0],
                        [13, [1500, 3000], 0], [14, [2000, 4000], 0], [15, [3000, 6000], 0], [16, [4000, 8000], 0],
                        [17, [5000, 10000], 0], [18, [6000, 12000], 0], [19, [8000, 16000], 0],
                        [20, [10000, 20000], 0], [21, [15000, 30000], 0], [22, [20000, 40000], 0],
                        [23, [30000, 60000], 0], [24, [40000, 80000], 0], [25, [50000, 100000], 0],
                        [26, [60000, 120000], 0], [27, [80000, 160000], 0], [28, [100000, 200000], 0],
                        [29, [150000, 300000], 0], [30, [200000, 400000], 0], [31, [250000, 500000], 0],
                        [32, [300000, 600000], 0], [33, [400000, 800000], 0], [34, [500000, 1000000], 0],
                        [35, [1000000, 2000000], 0], [36, [2000000, 4000000], 0]
                   ]
           },
    'mtt': {
        'standard':
            [
                [1, [10, 20], 0], [2, [15, 30], 0], [3, [20, 40], 0], [4, [30, 60], 5], [5, [40, 80], 8],
                [6, [50, 100], 10], [7, [75, 150], 15], [8, [100, 200], 20], [9, [125, 250], 25], [10, [150, 300], 30],
                [11, [200, 400], 40], [12, [250, 500], 50], [13, [300, 600], 60], [14, [400, 800], 80],
                [15, [500, 1000], 100], [16, [600, 1200], 120], [17, [700, 1400], 140], [18, [800, 1600], 160],
                [19, [1000, 2000], 200], [20, [1200, 2400], 250], [21, [1500, 3000], 300], [22, [1800, 3600], 350],
                [23, [2000, 4000], 400], [24, [2500, 5000], 500], [25, [3000, 6000], 600], [26, [3500, 7000], 700],
                [27, [4000, 8000], 800], [28, [5000, 10000], 1000], [29, [6000, 12000], 1200],
                [30, [8000, 16000], 1600], [31, [10000, 20000], 2000], [32, [12000, 24000], 2500],
                [33, [15000, 30000], 3000], [34, [20000, 40000], 4000], [35, [25000, 50000], 5000],
                [36, [30000, 60000], 6000], [37, [40000, 80000], 8000], [38, [50000, 100000], 10000],
                [39, [60000, 120000], 10000], [40, [80000, 160000], 15000], [41, [100000, 200000], 20000],
                [42, [120000, 240000], 25000], [43, [150000, 300000], 30000], [44, [200000, 400000], 40000],
                [45, [250000, 500000], 50000], [46, [300000, 600000], 60000], [47, [400000, 800000], 80000],
                [48, [500000, 1000000], 100000], [49, [600000, 1200000], 120000], [50, [800000, 1600000], 160000],
                [51, [1000000, 2000000], 200000], [52, [1500000, 3000000], 300000], [53, [2000000, 4000000], 400000],
                [54, [2500000, 5000000], 500000], [55, [3000000, 6000000], 600000], [56, [4000000, 8000000], 800000],
                [57, [5000000, 10000000], 1000000], [58, [6000000, 12000000], 1500000],
                [59, [8000000, 16000000], 1500000], [60, [10000000, 20000000], 2000000],
                [61, [15000000, 30000000], 3000000], [62, [20000000, 40000000], 4000000],
                [63, [25000000, 50000000], 5000000], [64, [30000000, 60000000], 6000000],
                [65, [40000000, 80000000], 8000000], [66, [50000000, 100000000], 10000000],
                [67, [60000000, 120000000], 10000000], [68, [80000000, 160000000], 15000000],
                [69, [100000000, 200000000], 20000000], [70, [150000000, 300000000], 30000000],
                [71, [200000000, 400000000], 40000000], [72, [250000000, 500000000], 50000000],
                [73, [300000000, 600000000], 60000000], [74, [400000000, 800000000], 80000000],
                [75, [500000000, 1000000000], 100000000], [76, [600000000, 1200000000], 100000000],
                [77, [800000000, 1600000000], 150000000], [78, [1000000000, 2000000000], 200000000],
                [79, [1500000000, 3000000000], 300000000], [80, [2000000000, 4000000000], 400000000]
            ],
    'turbo':
        [
            [1, [25, 50], 0], [2, [50, 100], 0], [3, [100, 200], 25], [4, [150, 300], 50], [5, [200, 400], 50],
            [6, [250, 500], 75], [7, [300, 600], 75], [8, [400, 800], 100], [9, [500, 1000], 100],
            [10, [600, 1200], 200], [11, [800, 1600], 200], [12, [1000, 2000], 300], [13, [1200, 2400], 300],
            [14, [1500, 3000], 400], [15, [2000, 4000], 500], [16, [2500, 5000], 800], [17, [3000, 6000], 1000],
            [18, [4000, 8000], 1000], [19, [5000, 10000], 1500], [20, [6000, 12000], 1500], [21, [8000, 16000], 2000],
            [22, [10000, 20000], 3000], [23, [12000, 24000], 3000], [24, [15000, 30000], 4000],
            [25, [20000, 40000], 5000], [26, [25000, 50000], 6000], [27, [30000, 60000], 8000],
            [28, [40000, 80000], 10000], [29, [50000, 100000], 15000], [30, [60000, 120000], 15000],
            [31, [80000, 160000], 20000], [32, [100000, 200000], 30000], [33, [120000, 240000], 30000],
            [34, [150000, 300000], 50000], [35, [200000, 400000], 50000], [36, [250000, 500000], 75000],
            [37, [300000, 600000], 100000], [38, [400000, 800000], 100000], [39, [500000, 1000000], 150000],
            [40, [600000, 1200000], 200000], [41, [800000, 1600000], 250000], [42, [1000000, 2000000], 300000],
            [43, [1500000, 3000000], 400000], [44, [2000000, 4000000], 500000], [45, [2500000, 5000000], 800000],
            [46, [3000000, 6000000], 1000000], [47, [4000000, 8000000], 1000000], [48, [5000000, 10000000], 1500000],
            [49, [6000000, 12000000], 1500000], [50, [8000000, 16000000], 2000000],
            [51, [10000000, 20000000], 3000000], [52, [15000000, 30000000], 3000000],
            [53, [20000000, 40000000], 5000000], [54, [30000000, 60000000], 10000000],
            [55, [40000000, 80000000], 10000000], [56, [50000000, 100000000], 15000000],
            [57, [60000000, 120000000], 15000000], [58, [80000000, 160000000], 20000000],
            [59, [100000000, 200000000], 30000000], [60, [150000000, 300000000], 30000000],
            [61, [200000000, 400000000], 50000000], [62, [300000000, 600000000], 100000000],
            [63, [400000000, 800000000], 100000000], [64, [500000000, 1000000000], 150000000],
            [65, [600000000, 1200000000], 150000000], [66, [800000000, 1600000000], 200000000],
            [67, [1000000000, 2000000000], 300000000], [68, [1500000000, 3000000000], 300000000],
            [69, [2000000000, 4000000000], 500000000], [70, [3000000000, 6000000000], 1000000000]
        ],
    'hyper_turbo':
        [
            [1, [50, 100], 0], [2, [100, 200], 0], [3, [150, 300], 50], [4, [200, 400], 50],
            [5, [300, 600], 75], [6, [400, 800], 100], [7, [500, 1000], 150], [8, [600, 1200], 200],
            [9, [800, 1600], 200], [10, [1000, 2000], 300], [11, [1500, 3000], 400], [12, [2000, 4000], 500],
            [13, [3000, 6000], 800], [14, [4000, 8000], 1000], [15, [5000, 10000], 1500],
            [16, [6000, 12000], 1500], [17, [8000, 16000], 2000], [18, [10000, 20000], 3000],
            [19, [15000, 30000], 4000], [20, [20000, 40000], 5000], [21, [30000, 60000], 8000],
            [22, [40000, 80000], 10000], [23, [50000, 100000], 15000], [24, [60000, 120000], 15000],
            [25, [80000, 160000], 20000], [26, [100000, 200000], 30000], [27, [150000, 300000], 40000],
            [28, [200000, 400000], 50000], [29, [300000, 600000], 80000], [30, [400000, 800000], 100000],
            [31, [500000, 1000000], 150000], [32, [600000, 1200000], 175000], [33, [800000, 1600000], 200000],
            [34, [1000000, 2000000], 300000], [35, [1500000, 3000000], 400000],
            [36, [2000000, 4000000], 500000], [37, [3000000, 6000000], 700000],
            [38, [4000000, 8000000], 1000000], [39, [5000000, 10000000], 1500000],
            [40, [6000000, 12000000], 1750000], [41, [8000000, 16000000], 2000000],
            [42, [10000000, 20000000], 3000000], [43, [15000000, 30000000], 4000000],
            [44, [20000000, 40000000], 5000000], [45, [30000000, 60000000], 7000000],
            [46, [40000000, 80000000], 10000000], [47, [50000000, 100000000], 15000000],
            [48, [60000000, 120000000], 17500000], [49, [80000000, 160000000], 20000000],
            [50, [100000000, 200000000], 30000000], [51, [150000000, 300000000], 40000000],
            [52, [200000000, 400000000], 50000000], [53, [300000000, 600000000], 70000000],
            [54, [400000000, 800000000], 100000000], [55, [500000000, 1000000000], 150000000],
            [56, [600000000, 1200000000], 175000000], [57, [800000000, 1600000000], 200000000],
            [58, [1000000000, 2000000000], 300000000], [59, [1500000000, 3000000000], 400000000],
            [60, [2000000000, 4000000000], 500000000]
        ]
    }
}


payment_structure = {
  "payment":
          [
            {"players": [1, 3], "position": {"first": 1.0, "second": 0.0, "third": 0.0}},
            {"players": [4, 6], "position": {"first": 0.7, "second": 0.3, "third": 0.0}},
            {"players": [7, 9], "position": {"first": 0.5, "second": 0.3, "third": 0.2}}
          ]
}
