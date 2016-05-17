'''
Created on Nov 4, 2010
Chapter 5 source file for Machine Learing in Action
@author: Peter

Modified on May 16, 2016 by shawn
A Kernel version of SVM using smo
'''

import numpy as np


def load_data(filename):
    dataMatrix = []; labelMatrix=[]
    f = open(filename)
    for line in f.readlines():
        lineToArray = line.strip().split('\t')
        dataMatrix.append([float(lineToArray[0]), float(lineToArray[1])])
        labelMatrix.append([float(lineToArray[2])])
    return np.array(dataMatrix), np.array(labelMatrix)


def random_select_aj(i, m):
    j = i
    while i == j:
        j = np.random.uniform(0, m)
    return j


def clip_a(ai, H, L):
    if ai > H:
        return H
    elif ai < L:
        return L
    return ai


def kernel(x, xi, k_tuple):
    m, n = np.shape(x)
    k = np.zeros((m, 1))
    if k_tuple[0] == 'linear':
        k = np.dot(x, xi.T)
    elif k_tuple[0] == 'rbf':
        for i in range(m):
            delta_row = x[i, :] - xi
            k[i] = np.dot(delta_row, delta_row.T)
        k = np.exp(-(k/k_tuple[1]**2))
    else:
        raise NameError('Kernel not recognized')
    return k


class Parameters:
    def __init__(self, data_matrix, label_matrix, c, tolerance, k_tuple):
        self.x = data_matrix
        self.y = label_matrix
        self.c = c
        self.tol = tolerance
        self.m = data_matrix.shape[0]
        self.a = np.zeros((self.m, 1))
        self.b = 0
        self.e_cache = np.zeros((self.m, 2))
        self.k = np.zeros((self.m, self.m))
        for i in range(self.m):
            self.k[:, i] = kernel(self.x, self.x[i], k_tuple).reshape(100,)


def calc_ei(p, i):
    f_xi = float(np.dot((p.a * p.y).T, p.k[:, i]) + p.b)
    ei = f_xi - float(p.y[i])
    return ei


def update_ei(p, i):
    ei = calc_ei(p, i)
    p.e_cache[i] = [1, ei]


def select_aj(i, p, ei):
    max_index = -1; ej = 0; max_delta_e = 0
    p.e_cache[i] = [1, ei]
    valid_indexes = np.transpose(np.nonzero(p.e_cache[:, 0]))
    if len(valid_indexes) > 1:
        for k in valid_indexes:
            if k == i: continue
            ek = calc_ei(p, k)
            delta_e = abs(ei - ek)
            if delta_e > max_delta_e:
                max_index = int(k); max_delta_e = delta_e; ej = ek
        return max_index, ej
    else:
        j = int(random_select_aj(i, p.m))
        ej = calc_ei(p, j)
    return j, ej


def inner_loop(i, p):
    ei = calc_ei(p, i)
    if ((p.a[i] < p.c) and (p.y[i] * ei < -p.tol)) or \
        ((p.a[i] > 0) and (p.y[i] * ei > p.tol)):

        j, ej = select_aj(i, p, ei)
        a_i_old = p.a[i].copy()
        a_j_old = p.a[j].copy()

        if p.y[i] != p.y[j]:
            L = max(0, p.a[j] - p.a[i])
            H = min(p.c, p.a[j] - p.a[i] + p.c)
        else:
            L = max(0, p.a[j] + p.a[i] - p.c)
            H = min(p.c, p.a[j] + p.a[i])
        if L == H: print('L == H'); return 0

        eta = float(p.k[i][i] + p.k[j][j] - 2 * p.k[i][j])
        if eta < 0: print('eta < 0'); return 0

        p.a[j] += p.y[j] * (ei - ej) / eta
        p.a[j] = clip_a(p.a[j], H, L)
        update_ei(p, j)

        if abs(p.a[j] - a_j_old) < 0.00001:
            print('j not moving enough, pick another i')
            return 0

        p.a[i] = p.a[i] + p.y[i] * p.y[j] * (a_j_old - p.a[j])
        update_ei(p, i)

        bi = p.b - (ei + p.y[i] * float(p.k[i][i]) * (p.a[i] - a_i_old) +
                  p.y[j] * float(p.k[j][i]) * (p.a[j] - a_j_old))
        bj = p.b - (ej + p.y[i] * float(p.k[i][j]) * (p.a[i] - a_i_old) +
                  p.y[j] * float(p.k[j][j]) * (p.a[j] - a_j_old))
        if (p.a[i] > 0) and (p.a[i] < p.c):
            p.b = bi
        elif (p.a[j] > 0) and (p.a[j] < p.c):
            p.b = bj
        else:
            p.b = (bi + bj) / 2.0
        return 1
    else: return 0


def smo_platt(x, y, c, tolerance, max_iter, k_tuple=('linear', 0)):
    p = Parameters(x, y, c, tolerance, k_tuple)
    iter = 0
    entire_set = False
    a_pairs_changed = 0

    while (iter < max_iter) and ((a_pairs_changed > 0) or (entire_set == False)):
        a_pairs_changed = 0
        if entire_set == False:
            for i in range(p.m):
                a_pairs_changed += inner_loop(i, p)
                print('full set, iter: %d, i: %d, pairs changed: %d' % (iter, i, a_pairs_changed))
            iter += 1
        else:
            support_vector_indexes = np.transpose(np.nonzero((p.a > 0)*(p.a < c)))[:, 0]
            for i in support_vector_indexes:
                a_pairs_changed += inner_loop(i, p)
                print('support_vectors, iter: %d, i: %d, pairs changed: %d' % (iter, i, a_pairs_changed))
            iter += 1
        if entire_set == False: entire_set = True
        print('iteration: %d' % iter)
    return p.a, p.b