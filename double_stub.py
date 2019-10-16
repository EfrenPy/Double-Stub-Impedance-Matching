# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 10:22:44 2019

@author: efren
"""

import numpy as np
import scipy.optimize as sco
import sys as sys

""" A continuacion tomamos los datos necsarios 
"""
#l  = float(input('Enter distance from charge to first stub (lambda units):'))
#d    =float( input('Enter distance within stubs (lambda units):'))
#zz = input('Enter charge impedance a+bj ( a,b ):')
#Z0   =float( input('Enter characteristic impedance of the line (real):'))
#Z0s   = float(input('Enter characteristic impedance of the stubs (real):'))
#precision    =float(input('Enter the tolerance for stub length :'))
#shortopen    =float(input('Stubs short-circuited (1) or open-circuited (2):'))

""" Datos para hacer las pruebas sin insertarlos cada vez
"""
l=0.07
d=3./8.
zz='38.9,-26.7'
Z0=50
Z0s=50
shortopen=1
precision=1e-8

""" Pasamos de impedancias a admitancias
"""
mitad=int(len(zz)/2)
ZL=complex(float(zz[:mitad-1]),float(zz[mitad:]))
Y0=1/Z0
Y0s=1/Z0s
YL=1/ZL


def desplazamiento(YL_f,l_f):
    """ Función para desplazar admitancia una distancia l_f lambdas
    """
    num=(YL_f/Y0)*np.cos(2*np.pi*l_f)+1j*np.sin(2*np.pi*l_f)
    den=np.cos(2*np.pi*l_f)+1j*np.sin(2*np.pi*l_f)*(YL_f/Y0)
    YLd=Y0*num/den
    return YLd

if shortopen==1:
    
    def stub(l_f):
        """ Calcula la Y_s que aplica el stub a la lina (corto)
        """
        return -1j*Y0s*cot(2*np.pi*l_f)
    
elif shortopen==2:
    
    def stub(l_f):
        """ Calcula la Y_s que aplica el stub a la lina (abierto)
        """
        return 1j*Y0s*np.tan(2*np.pi*l_f)
    
else:
    sys.exit('Please, define the stubs correctly')

def cot(x):
    """ Cotangente (no definida en numpy)
    """
    return np.cos(x)/np.sin(x)

def funcion(l_f):
    """ Función a minimizar para obtener parte real 
    de admitancia=1, de esta forma obtenemos l1
    """
    YLs=stub(l_f)
    YLb=YLa+YLs
    YLc=desplazamiento(YLb,d)
    f=YLc.real/Y0-1.
    return f

def func(l_f):
    """ Función a minimizar para obtener
    l2 una vez conocido l1
    """
    YLs=stub(l1)
    YLb=YLa+YLs
    YLc=desplazamiento(YLb,d)
    f=YLc.imag+stub(l_f).imag
    return f

z=[0.]
long=[]
for i in range(1,500): #bucle para inicializar la solución a valores distintos
    lini=0.001*i                #Inicializamos la l1
    YLa=desplazamiento(YL,l)    #Aplicamos el desplazamiento hasta el stub1
    sol=sco.fsolve(funcion,lini,xtol=precision) #Resolvemos la función
    if 0<sol[0]<0.5 and np.abs(sol[0]-z[-1])>precision:
        z.append(sol[0])    #Guardamos la solución

""" A continuación nos deshacemos de las soluciones repetidas
"""        
z.pop(0)
index=[]
for j in range(1,len(z)):
    if np.abs(z[0]-z[j])<precision:
        index.append(j)
index.sort(reverse=True)
for i in index:
    z.pop(i)
index=[]
for j in range(2,len(z)):
    if np.abs(z[1]-z[j])<precision:
        index.append(j)
index.sort(reverse=True)
for i in index:
    z.pop(i)

#======================== Calculo del segundo stub ==============================
""" Mismo procedimiento que para el primero
pero minimizando la función: 'func'
"""
w=[0.]
for l1 in z:
     for i in range(1,500):
        lini=0.001*i
        YLa=desplazamiento(YL,l)
        sol=sco.fsolve(func,lini,xtol=1e-8)
        if 0<sol[0]<0.5 :
            w.append(sol[0])
w.pop(0)
w.pop(0)
w.pop(-1)
index=[]
for j in range(1,len(w)):
    if np.abs(w[0]-w[j])<precision:
        index.append(j)
index.sort(reverse=True)
for i in index:
    w.pop(i)
index=[]
for j in range(2,len(w)):
    if np.abs(w[1]-w[j])<precision:
        index.append(j)
index.sort(reverse=True)
for i in index:
    w.pop(i)
    
""" Mostramos los resultados en pantalla
"""
print('The length for the stubs are (in lambdas):')
print('Case 1: l1 = ',z[0],', l2 = ',w[0])
print('Case 2: l1 = ',z[1],', l2 = ',w[1])
print('The precision for this is: ', precision)
