class BaseRecoilData:
    sampling_rate_ms = 8
    Shift_Boost = 1.0

    Strength_Normal = 100
    Strength_2x = 100
    Strength_3x = 100
    Strength_4x = 100
    Strength_6x = 100
    Strength_8x = 100
    Strength_15x = 100

    scope_multipliers =     {
        'Scope1': 1.0,
        'Scope2': 1.75,
        'Scope3': 2.65,
        'Scope4': 3.65,
        'Scope6': 2.65,
        'Scope8': 2.65,
        'ScopeKH1': 1.0,
        'ScopeKH4': 3.65
}

    grips =     {
        'NONE': 1.25,
        'tcDung': 1.02,
        'tcHong': 1.07,
        'tcLaser': 1.3,
        'tcNamChat': 1.05,
        'tcNghieng': 1.1,
        'tcNhe': 1.15
}

    accessories =     {
        'NONE': 1.25,
        'ATLsmg': 1.15,
        'AnTiaLua': 1.06,
        'GGiatSMG': 1,
        'GThanhSMG': 1.25,
        'GiamGiat': 0.95,
        'GiamRung': 1.06
}

    Weapons = {
        'AUG': {
            'BaseTable': [[10, 1], [4.15, 49], [4.75, 50], [5.85, 50], [6.05, 50], [6.15, 50], [6.05, 51], [6, 51], [6, 51]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.67},
        },
        'ACE32': {
            'BaseTable': [[15, 1], [4, 55], [4.4, 55], [4.5, 55], [4.85, 55], [4.95, 55], [5.15, 55], [5.25, 55], [5.25, 55]],
            'stance_multipliers': {'Stand': 1.32, 'Crouch': 1.0, 'Prone': 0.7},
        },
        'AKM': {
            'BaseTable': [[15, 1], [3.65, 62], [4.5, 62], [4.7, 62], [5, 62], [5.1, 62], [5.2, 62], [5.35, 62], [5.25, 62]],
            'stance_multipliers': {'Stand': 1.3, 'Crouch': 1.0, 'Prone': 0.65},
        },
        'BERYL': {
            'BaseTable': [[15, 1], [5.1, 53], [5.5, 54], [6.5, 54], [7, 54], [7.2, 54], [7.2, 54], [7.2, 54], [7.2, 54]],
            'stance_multipliers': {'Stand': 1.22, 'Crouch': 1.0, 'Prone': 0.71},
        },
        'BIZON': {
            'BaseTable': [[1.95, 10], [2.05, 20], [2.41, 520]],
            'stance_multipliers': {'Stand': 1.27, 'Crouch': 1.0, 'Prone': 0.83},
        },
        'DP28': {
            'BaseTable': [[15, 1], [1.45, 88], [2, 88], [2.1, 88], [2.2, 88], [2.1, 88], [2.2, 88], [2.1, 88]],
            'stance_multipliers': {'Stand': 2.7, 'Crouch': 1.0, 'Prone': 0.1},
        },
        'FAMAS': {
            'BaseTable': [[15, 1], [3.5, 40], [4.4, 41], [5, 41], [5.3, 41], [5.25, 41], [5.2, 41], [5.25, 41], [4.9, 41]],
            'stance_multipliers': {'Stand': 1.3, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'G36C': {
            'BaseTable': [[15, 1], [3.3, 53], [4.7, 54], [4.95, 54], [5, 54], [5.1, 54], [5.1, 54], [5.1, 54], [5.1, 54]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.72},
        },
        'GROZA': {
            'BaseTable': [[15, 1], [3.3, 49], [3.55, 50], [3.75, 50], [4.55, 50], [4.35, 50], [4.45, 50], [4.35, 50], [4.35, 50]],
            'stance_multipliers': {'Stand': 1.35, 'Crouch': 1.0, 'Prone': 0.72},
        },
        'JS9': {
            'BaseTable': [[5, 1], [2, 41], [2.45, 41], [2.45, 41], [2.6, 41], [2.55, 41], [2.5, 41], [2.85, 41], [2.8, 41]],
            'stance_multipliers': {'Stand': 1.3, 'Crouch': 1.0, 'Prone': 0.8},
        },
        'K2': {
            'BaseTable': [[10, 1], [3.85, 53], [4.45, 54], [4.65, 54], [5.2, 54], [4.7, 54], [4.7, 54], [4.75, 54], [4.75, 54]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'M249': {
            'BaseTable': [[1.95, 40], [2.15, 110], [1.75, 1205], [1.6, 52]],
            'stance_multipliers': {'Stand': 1.5, 'Crouch': 1.0, 'Prone': 0.2},
        },
        'M416': {
            'BaseTable': [[15, 1], [3.65, 53], [4.45, 54], [4.75, 54], [4.7, 54], [4.75, 54], [4.75, 54], [4.7, 54], [4.7, 54]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'MG3': {
            'BaseTable': [[25, 1], [1.65, 40], [1.55, 60], [0.95, 100], [0.9, 100], [0.9, 100], [0.9, 100], [0.9, 100], [0.9, 100], [0.9, 120]],
            'stance_multipliers': {'Stand': 2.1, 'Crouch': 1.0, 'Prone': 0.45},
        },
        'MP5K': {
            'BaseTable': [[2, 1], [2.65, 41], [3.0, 42], [3.15, 42], [3.1, 42], [3.15, 42], [3.2, 42], [3.25, 42], [3.2, 42]],
            'stance_multipliers': {'Stand': 1.21, 'Crouch': 1.0, 'Prone': 0.85},
        },
        'MP9': {
            'BaseTable': [[1, 1], [2.4, 31], [2.3, 32], [2.35, 32], [1.8, 32], [1.8, 32], [1.7, 32], [1.5, 32], [1.5, 32]],
            'stance_multipliers': {'Stand': 1.28, 'Crouch': 1.0, 'Prone': 0.81},
        },
        'P90': {
            'BaseTable': [[2, 1], [2.75, 45], [2.85, 46], [2.45, 46], [2.2, 46], [2.15, 46], [2.15, 46], [2.15, 46], [2.15, 46]],
            'stance_multipliers': {'Stand': 1.21, 'Crouch': 1.0, 'Prone': 0.85},
        },
        'QBZ': {
            'BaseTable': [[35, 1], [3.5, 55], [4.05, 56], [4.6, 56], [4.85, 56], [4.95, 56], [4.95, 56], [4.8, 56], [5.35, 56]],
            'stance_multipliers': {'Stand': 1.19, 'Crouch': 1.0, 'Prone': 0.74},
        },
        'SCARL': {
            'BaseTable': [[25, 1], [2.85, 55], [4.3, 56], [4.4, 56], [4.4, 56], [4.6, 56], [4.7, 56], [4.6, 56], [4.6, 56]],
            'stance_multipliers': {'Stand': 1.19, 'Crouch': 1.0, 'Prone': 0.72},
        },
        'TOMMY': {
            'BaseTable': [[2, 1], [2.45, 63], [3.95, 64], [4.1, 64], [4.15, 64], [4.2, 64], [4.15, 64], [4.2, 64], [4.15, 64]],
            'stance_multipliers': {'Stand': 1.25, 'Crouch': 1.0, 'Prone': 0.85},
        },
        'UMP': {
            'BaseTable': [[2.25, 20], [2.25, 20], [2.65, 20], [2.75, 70], [2.75, 70], [2.75, 30], [3.1, 170]],
            'stance_multipliers': {'Stand': 1.28, 'Crouch': 1.0, 'Prone': 0.85},
        },
        'UZI': {
            'BaseTable': [[1, 10], [1, 10], [1.2, 20], [2.3, 20], [2.7, 10], [3.0, 16], [2.8, 120]],
            'stance_multipliers': {'Stand': 1.25, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'VECTOR': {
            'BaseTable': [[2.6, 10], [2.6, 10], [3.1, 20], [3.5, 20], [4.1, 10], [5.2, 20], [5.5, 20], [5.5, 120]],
            'stance_multipliers': {'Stand': 1.25, 'Crouch': 1.0, 'Prone': 0.8},
        },
        'VSS': {
            'BaseTable': [[2, 30], [5, 20], [6.5, 20], [7.5, 20], [9.9, 130]],
            'stance_multipliers': {'Stand': 1.38, 'Crouch': 1.0, 'Prone': 0.75},
        },
        'AWM': {
            'BaseTable': [[1, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'DRAGUNOV': {
            'BaseTable': [[15, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'KAR98K': {
            'BaseTable': [[1, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'LYNX': {
            'BaseTable': [[1, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'M24': {
            'BaseTable': [[1, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'MINI14': {
            'BaseTable': [[1, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'MK12': {
            'BaseTable': [[1, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'MK14': {
            'BaseTable': [[1.7, 50], [1.9, 50], [1.95, 50], [2.5, 50], [2.6, 50], [2.6, 50], [2.4, 50], [2.3, 50]],
            'stance_multipliers': {'Stand': 1.25, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'MOSIN': {
            'BaseTable': [[1, 1]],
            'stance_multipliers': {'Stand': 1.25, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'QBU': {
            'BaseTable': [[1, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'SKS': {
            'BaseTable': [[1, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'SLR': {
            'BaseTable': [[1, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'WIN94': {
            'BaseTable': [[1, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'DBS': {
            'BaseTable': [[55, 1]],
            'stance_multipliers': {'Stand': 1.0, 'Crouch': 1.0, 'Prone': 1.0},
        },
        'M16A4': {
            'BaseTable': [[55, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'MK47': {
            'BaseTable': [[35, 1]],
            'stance_multipliers': {'Stand': 1.2, 'Crouch': 1.0, 'Prone': 0.73},
        },
        'O12': {
            'BaseTable': [[30, 1]],
            'stance_multipliers': {'Stand': 1.0, 'Crouch': 1.0, 'Prone': 1.0},
        },
        'S12K': {
            'BaseTable': [[30, 1]],
            'stance_multipliers': {'Stand': 1.0, 'Crouch': 1.0, 'Prone': 1.0},
        },
        'S1897': {
            'BaseTable': [[30, 1]],
            'stance_multipliers': {'Stand': 1.0, 'Crouch': 1.0, 'Prone': 1.0},
        },
        'S686': {
            'BaseTable': [[30, 1]],
            'stance_multipliers': {'Stand': 1.0, 'Crouch': 1.0, 'Prone': 1.0},
        },
    }
