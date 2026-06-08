import React, { useState, useEffect } from 'react';
import { Layers, Plus, Trash2, PlusCircle, ShoppingCart, Activity } from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

import { apiFetch, API_BASE } from '../lib/apiClient';

export default function RecipeInventory() {
  const { isMobile } = useResponsive();
  const [activeTab, setActiveTab] = useState('inventory'); // 'inventory', 'recipes', or 'audit'
  
  // Ingredients State
  const [ingredients, setIngredients] = useState([]);
  const [loadingIng, setLoadingIng] = useState(true);
  
  // Add/Buy Ingredient State
  const [newIngName, setNewIngName] = useState('');
  const [newIngQty, setNewIngQty] = useState('');
  const [newIngUnit, setNewIngUnit] = useState('kg');
  const [newIngUnitPrice, setNewIngUnitPrice] = useState('');
  
  const [purchaseIngId, setPurchaseIngId] = useState('');
  const [purchaseQty, setPurchaseQty] = useState('');
  const [purchaseCost, setPurchaseCost] = useState('');

  // Stock Audit State
  const [auditCounts, setAuditCounts] = useState({});
  const [auditNotes, setAuditNotes] = useState('');
  const [pastAudits, setPastAudits] = useState([]);
  const [loadingAudits, setLoadingAudits] = useState(false);
  
  // Recipes State
  const [menuItems, setMenuItems] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [recipeIngredients, setRecipeIngredients] = useState([]);
  
  // Recipe Form State
  const [selectedMenuItem, setSelectedMenuItem] = useState('');
  const [instructions, setInstructions] = useState('');
  const [recipeIngsList, setRecipeIngsList] = useState([]); // [{ingredient: id, quantity: value}]

  useEffect(() => {
    fetchIngredients();
    fetchRecipesData();
  }, []);

  useEffect(() => {
    if (activeTab === 'audit') {
      fetchPastAudits();
      const initialCounts = {};
      ingredients.forEach(ing => {
        initialCounts[ing.id] = '';
      });
      setAuditCounts(initialCounts);
    }
  }, [activeTab]);

  const fetchPastAudits = async () => {
    try {
      setLoadingAudits(true);
      const res = await apiFetch(`/stock-audits/`);
      const data = await res.json();
      setPastAudits(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingAudits(false);
    }
  };

  const handleSubmitAudit = async () => {
    const items = ingredients.map(ing => {
      const enteredVal = auditCounts[ing.id];
      const actualStock = enteredVal !== '' && enteredVal !== undefined ? parseFloat(enteredVal) : parseFloat(ing.stock_quantity);
      return {
        ingredient: ing.id,
        actual_stock: actualStock
      };
    });

    try {
      const res = await apiFetch(`/stock-audits/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          notes: auditNotes || 'Sayım Günü Ayarlaması',
          items: items
        })
      });

      if (res.ok) {
        alert('Stok sayımı başarıyla onaylandı ve stok miktarları güncellendi.');
        setAuditNotes('');
        const resetCounts = {};
        ingredients.forEach(ing => {
          resetCounts[ing.id] = '';
        });
        setAuditCounts(resetCounts);
        fetchIngredients();
        fetchPastAudits();
      } else {
        alert('Sayım kaydedilemedi.');
      }
    } catch (err) {
      console.error(err);
      alert('Sayım kaydedilirken bir hata oluştu.');
    }
  };

  const fetchIngredients = async () => {
    try {
      setLoadingIng(true);
      const res = await apiFetch(`/ingredients/`);
      const data = await res.json();
      setIngredients(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingIng(false);
    }
  };

  const fetchRecipesData = async () => {
    try {
      const [itemsRes, recsRes, recIngsRes] = await Promise.all([
        apiFetch('/menu-items/'),
        apiFetch('/recipes/'),
        apiFetch('/recipe-ingredients/'),
      ]);
      const items = await itemsRes.json();
      const recs = await recsRes.json();
      const recIngs = await recIngsRes.json();
      setMenuItems(items);
      setRecipes(recs);
      setRecipeIngredients(recIngs);
      if (items.length > 0) {
        setSelectedMenuItem(items[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddIngredient = async (e) => {
    e.preventDefault();
    if (!newIngName) return;

    try {
      const res = await apiFetch(`/ingredients/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newIngName,
          stock_quantity: parseFloat(newIngQty || 0),
          unit: newIngUnit,
          unit_price: parseFloat(newIngUnitPrice || 0)
        })
      });
      if (res.ok) {
        setNewIngName('');
        setNewIngQty('');
        setNewIngUnitPrice('');
        fetchIngredients();
        alert('Malzeme başarıyla eklendi.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handlePurchaseStock = async (e) => {
    e.preventDefault();
    if (!purchaseIngId || !purchaseQty) return;

    const ing = ingredients.find(i => i.id === parseInt(purchaseIngId));
    if (!ing) return;

    const updatedQty = parseFloat(ing.stock_quantity) + parseFloat(purchaseQty);
    const cost = purchaseCost && parseFloat(purchaseCost) > 0 ? parseFloat(purchaseCost) : 0;
    
    let updatedUnitPrice = parseFloat(ing.unit_price || 0);
    if (cost > 0 && parseFloat(purchaseQty) > 0) {
      updatedUnitPrice = cost / parseFloat(purchaseQty);
    }

    try {
      // 1. Update ingredient stock and unit price
      const ingPayload = { stock_quantity: updatedQty };
      if (cost > 0) {
        ingPayload.unit_price = updatedUnitPrice;
      }

      const ingRes = await apiFetch(`/ingredients/${purchaseIngId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ingPayload)
      });

      // 2. Automatically log expense if cost is entered
      if (cost > 0) {
        await apiFetch(`/expenses/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: `${ing.name} Stok Alımı (${purchaseQty} ${ing.unit})`,
            amount: cost,
            category: 'Gıda Malzemesi'
          })
        });
      }

      if (ingRes.ok) {
        setPurchaseIngId('');
        setPurchaseQty('');
        setPurchaseCost('');
        fetchIngredients();
        alert('Stok başarıyla güncellendi ve gider kaydedildi.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddIngToRecipeForm = () => {
    setRecipeIngsList([...recipeIngsList, { ingredient: ingredients[0]?.id, quantity: '' }]);
  };

  const handleRemoveIngFromRecipeForm = (index) => {
    setRecipeIngsList(recipeIngsList.filter((_, i) => i !== index));
  };

  const handleRecipeFormChange = (index, field, value) => {
    const list = [...recipeIngsList];
    list[index][field] = value;
    setRecipeIngsList(list);
  };

  const handleCreateRecipe = async (e) => {
    e.preventDefault();
    if (!selectedMenuItem) return;

    try {
      // Create Recipe
      const recRes = await apiFetch(`/recipes/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          menu_item: parseInt(selectedMenuItem),
          instructions
        })
      });

      if (recRes.ok) {
        const recipeObj = await recRes.json();
        
        // Add all recipe ingredients
        await Promise.all(recipeIngsList.map(item => {
          const ing = ingredients.find(i => i.id === parseInt(item.ingredient));
          return apiFetch('/recipe-ingredients/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              recipe: recipeObj.id,
              ingredient: parseInt(item.ingredient),
              quantity: parseFloat(item.quantity),
              unit: ing?.unit || 'pcs'
            })
          });
        }));

        setInstructions('');
        setRecipeIngsList([]);
        fetchRecipesData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Sub tabs */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <button 
          className={`btn ${activeTab === 'inventory' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('inventory')}
          style={{ padding: '8px 16px', fontSize: '13px' }}
        >
          Stok Durumu & Satın Alım
        </button>
        <button 
          className={`btn ${activeTab === 'recipes' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('recipes')}
          style={{ padding: '8px 16px', fontSize: '13px' }}
        >
          Reçete Yönetimi
        </button>
        <button 
          className={`btn ${activeTab === 'audit' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('audit')}
          style={{ padding: '8px 16px', fontSize: '13px' }}
        >
          Stok Sayımı (Sayım Günü)
        </button>
      </div>

      {activeTab === 'inventory' && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.5fr 1fr', gap: isMobile ? '16px' : '24px' }}>
          {/* Ingredients list */}
          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Malzeme Stok Listesi</h3>
            {loadingIng ? (
              <div className="spinner"></div>
            ) : (
              <div className="table-container">
                <table className="mgmt-table">
                  <thead>
                    <tr>
                      <th>Malzeme Adı</th>
                      <th style={{ textAlign: 'right' }}>Mevcut Stok</th>
                      <th>Birim</th>
                      <th style={{ textAlign: 'right' }}>Birim Fiyatı</th>
                      <th>Durum</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ingredients.map(ing => {
                      const qty = parseFloat(ing.stock_quantity);
                      let statusBadge = 'badge-success';
                      let statusText = 'Yeterli';
                      if (qty <= 5) {
                        statusBadge = 'badge-danger';
                        statusText = 'Kritik Stok';
                      } else if (qty <= 15) {
                        statusBadge = 'badge-warning';
                        statusText = 'Azalıyor';
                      }
                      return (
                        <tr key={ing.id}>
                          <td style={{ fontWeight: '500' }}>{ing.name}</td>
                          <td style={{ fontWeight: '700', textAlign: 'right' }}>{qty.toLocaleString('tr-TR')}</td>
                          <td>{ing.unit}</td>
                          <td style={{ fontWeight: '600', textAlign: 'right' }}>{parseFloat(ing.unit_price || 0).toLocaleString('tr-TR')} ₺</td>
                          <td>
                            <span className={`badge ${statusBadge}`}>{statusText}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Actions panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Purchase Form */}
            <div className="card">
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShoppingCart size={18} /> Stok Satın Alımı Yap
              </h3>
              <form onSubmit={handlePurchaseStock}>
                <div className="form-group">
                  <label>Malzeme Seçin</label>
                  <select className="form-control form-select" value={purchaseIngId} onChange={(e) => setPurchaseIngId(e.target.value)} required>
                    <option value="" disabled>Seçiniz...</option>
                    {ingredients.map(i => (
                      <option key={i.id} value={i.id}>{i.name} ({i.unit})</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Alınan Miktar</label>
                  <input type="number" step="0.01" className="form-control" placeholder="Miktar" value={purchaseQty} onChange={(e) => setPurchaseQty(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Toplam Maliyet (TL)</label>
                  <input type="number" step="0.01" className="form-control" placeholder="örn: 250" value={purchaseCost} onChange={(e) => setPurchaseCost(e.target.value)} />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '12px' }}>
                  Satın Alımı Tamamla
                </button>
              </form>
            </div>

            {/* Create Ingredient Form */}
            <div className="card">
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Yeni Malzeme Tanımla</h3>
              <form onSubmit={handleAddIngredient}>
                <div className="form-group">
                  <label>Malzeme Adı</label>
                  <input type="text" className="form-control" placeholder="örn: Domates" value={newIngName} onChange={(e) => setNewIngName(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Başlangıç Stok</label>
                  <input type="number" className="form-control" placeholder="0" value={newIngQty} onChange={(e) => setNewIngQty(e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Birim</label>
                  <select className="form-control form-select" value={newIngUnit} onChange={(e) => setNewIngUnit(e.target.value)}>
                    <option value="kg">Kilogram (kg)</option>
                    <option value="litre">Litre (L)</option>
                    <option value="adet">Adet (pcs)</option>
                    <option value="paket">Paket</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Birim Fiyatı (TL)</label>
                  <input type="number" step="0.01" className="form-control" placeholder="örn: 45.00" value={newIngUnitPrice} onChange={(e) => setNewIngUnitPrice(e.target.value)} />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '12px' }}>
                  Malzeme Kaydet
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'recipes' && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.5fr 1fr', gap: isMobile ? '16px' : '24px' }}>
          {/* Recipes list */}
          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Menü Reçeteleri</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {menuItems.map(item => {
                const recipe = recipes.find(r => r.menu_item === item.id);
                const ings = recipe ? recipeIngredients.filter(ri => ri.recipe === recipe.id) : [];
                return (
                  <div key={item.id} style={{ padding: '16px', border: '1px solid var(--panel-border)', borderRadius: '12px', background: 'rgba(255,255,255,0.02)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: '600', fontSize: '16px' }}>{item.name}</span>
                      {recipe ? (
                        <span className="badge badge-success">Reçete Aktif</span>
                      ) : (
                        <span className="badge badge-danger">Reçete Yok</span>
                      )}
                    </div>
                    {recipe && (
                      <div style={{ marginTop: '12px', fontSize: '14px' }}>
                        <p style={{ color: 'var(--text-muted)' }}><strong>Hazırlanış:</strong> {recipe.instructions}</p>
                        <div style={{ marginTop: '8px' }}>
                          <strong>Malzemeler:</strong>
                          <ul style={{ paddingLeft: '20px', marginTop: '4px', color: 'var(--text-muted)' }}>
                            {ings.map(ri => {
                              const ing = ingredients.find(i => i.id === ri.ingredient);
                              return (
                                <li key={ri.id}>{ri.quantity} {ri.unit} - {ing?.name}</li>
                              );
                            })}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Add/Edit Recipe Form */}
          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Reçete Oluştur</h3>
            <form onSubmit={handleCreateRecipe}>
              <div className="form-group">
                <label>Menü Ürünü</label>
                <select className="form-control form-select" value={selectedMenuItem} onChange={(e) => setSelectedMenuItem(e.target.value)} required>
                  {menuItems.map(item => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Hazırlanış Açıklaması</label>
                <textarea className="form-control" rows="3" placeholder="Yemeğin yapılış adımları..." value={instructions} onChange={(e) => setInstructions(e.target.value)}></textarea>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <label style={{ fontSize: '13px' }}>Malzemeler</label>
                  <button type="button" className="action-icon-btn" onClick={handleAddIngToRecipeForm}>
                    <Plus size={16} /> Ekle
                  </button>
                </div>

                {recipeIngsList.map((item, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                    <select 
                      className="form-control form-select" 
                      value={item.ingredient} 
                      onChange={(e) => handleRecipeFormChange(idx, 'ingredient', e.target.value)}
                      style={{ flex: 2 }}
                    >
                      {ingredients.map(ing => (
                        <option key={ing.id} value={ing.id}>{ing.name} ({ing.unit})</option>
                      ))}
                    </select>
                    <input 
                      type="number" 
                      step="0.01" 
                      className="form-control" 
                      placeholder="Miktar" 
                      value={item.quantity}
                      onChange={(e) => handleRecipeFormChange(idx, 'quantity', e.target.value)}
                      style={{ flex: 1 }}
                      required
                    />
                    <button type="button" className="action-icon-btn delete" onClick={() => handleRemoveIngFromRecipeForm(idx)}>
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '12px' }}>
                Reçeteyi Kaydet
              </button>
            </form>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '2.2fr 1fr', gap: isMobile ? '16px' : '24px' }}>
            
            {/* Audit Entry Table */}
            <div className="card">
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={18} /> Malzeme Fiziki Stok Sayımı
              </h3>
              <div className="table-container">
                <table className="mgmt-table">
                  <thead>
                    <tr>
                      <th>Malzeme Adı</th>
                      <th style={{ textAlign: 'right' }}>Sistem Stoğu</th>
                      <th style={{ width: '120px' }}>Fiziki Sayım</th>
                      <th>Birim</th>
                      <th style={{ textAlign: 'right' }}>Birim Fiyatı</th>
                      <th style={{ textAlign: 'right' }}>Fark</th>
                      <th style={{ textAlign: 'right' }}>Maliyet Farkı</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ingredients.map(ing => {
                      const systemStock = parseFloat(ing.stock_quantity);
                      const unitPrice = parseFloat(ing.unit_price || 0);
                      const enteredVal = auditCounts[ing.id];
                      const actualStock = enteredVal !== '' && enteredVal !== undefined ? parseFloat(enteredVal) : systemStock;
                      
                      const variance = actualStock - systemStock;
                      const costDiff = variance * unitPrice;
                      
                      return (
                        <tr key={ing.id}>
                          <td style={{ fontWeight: '500' }}>{ing.name}</td>
                          <td style={{ textAlign: 'right', fontWeight: '600' }}>{systemStock.toLocaleString('tr-TR')}</td>
                          <td>
                            <input 
                              type="number" 
                              step="0.01"
                              className="form-control"
                              style={{ padding: '6px 10px', fontSize: '13px', margin: '0' }}
                              placeholder={systemStock.toString()}
                              value={enteredVal || ''}
                              onChange={(e) => {
                                setAuditCounts({
                                  ...auditCounts,
                                  [ing.id]: e.target.value
                                });
                              }}
                            />
                          </td>
                          <td>{ing.unit}</td>
                          <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>{unitPrice.toLocaleString('tr-TR')} ₺</td>
                          <td style={{ 
                            textAlign: 'right', 
                            fontWeight: '700',
                            color: variance === 0 ? 'var(--text-muted)' : variance > 0 ? 'var(--success)' : 'var(--danger)'
                          }}>
                            {variance > 0 ? `+${variance.toLocaleString('tr-TR')}` : variance.toLocaleString('tr-TR')}
                          </td>
                          <td style={{ 
                            textAlign: 'right', 
                            fontWeight: '700',
                            color: costDiff === 0 ? 'var(--text-muted)' : costDiff > 0 ? 'var(--success)' : 'var(--danger)'
                          }}>
                            {costDiff > 0 ? `+${costDiff.toLocaleString('tr-TR')}` : costDiff.toLocaleString('tr-TR')} ₺
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Audit Summary & Submit Form */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="card">
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Sayım Özeti</h3>
                
                {(() => {
                  let totalVarianceCost = 0;
                  let totalSurplusCost = 0;
                  let totalLossCost = 0;
                  let discrepancyCount = 0;

                  ingredients.forEach(ing => {
                    const systemStock = parseFloat(ing.stock_quantity);
                    const unitPrice = parseFloat(ing.unit_price || 0);
                    const enteredVal = auditCounts[ing.id];
                    const actualStock = enteredVal !== '' && enteredVal !== undefined ? parseFloat(enteredVal) : systemStock;
                    const variance = actualStock - systemStock;
                    const costDiff = variance * unitPrice;

                    totalVarianceCost += costDiff;
                    if (variance > 0) totalSurplusCost += costDiff;
                    if (variance < 0) totalLossCost += costDiff;
                    if (variance !== 0) discrepancyCount++;
                  });

                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--panel-border)', paddingBottom: '8px' }}>
                        <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Farklı Çıkan Ürün:</span>
                        <strong style={{ fontSize: '14px' }}>{discrepancyCount} Malzeme</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--panel-border)', paddingBottom: '8px' }}>
                        <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Toplam Fazla (Surplus):</span>
                        <strong style={{ color: 'var(--success)', fontSize: '14px' }}>+{totalSurplusCost.toLocaleString('tr-TR')} ₺</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--panel-border)', paddingBottom: '8px' }}>
                        <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Toplam Açık (Loss/Fire):</span>
                        <strong style={{ color: 'var(--danger)', fontSize: '14px' }}>{totalLossCost.toLocaleString('tr-TR')} ₺</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '4px' }}>
                        <span style={{ fontWeight: '600', fontSize: '14px' }}>Net Sayım Farkı:</span>
                        <strong style={{ 
                          fontSize: '18px', 
                          color: totalVarianceCost === 0 ? 'var(--text-main)' : totalVarianceCost > 0 ? 'var(--success)' : 'var(--danger)'
                        }}>
                          {totalVarianceCost > 0 ? '+' : ''}{totalVarianceCost.toLocaleString('tr-TR')} ₺
                        </strong>
                      </div>

                      <div className="form-group" style={{ marginTop: '10px' }}>
                        <label>Sayım Notu / Açıklama</label>
                        <input 
                          type="text" 
                          className="form-control" 
                          placeholder="örn: Aylık Olağan Stok Sayımı" 
                          value={auditNotes}
                          onChange={(e) => setAuditNotes(e.target.value)}
                        />
                      </div>

                      <button 
                        className="btn btn-primary" 
                        style={{ width: '100%', marginTop: '8px' }}
                        onClick={handleSubmitAudit}
                      >
                        Sayımı Onayla ve Stoğu Güncelle
                      </button>
                    </div>
                  );
                })()}
              </div>
            </div>

          </div>

          {/* Past Audits Logs History */}
          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Geçmiş Stok Sayımları (Fiyat Farkı Raporları)</h3>
            {loadingAudits ? (
              <div className="spinner"></div>
            ) : pastAudits.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)', fontSize: '13px' }}>
                Henüz geçmiş bir sayım kaydı bulunmuyor.
              </div>
            ) : (
              <div className="table-container">
                <table className="mgmt-table">
                  <thead>
                    <tr>
                      <th>Tarih</th>
                      <th>Sayım Açıklaması</th>
                      <th style={{ textAlign: 'right' }}>Toplam Maliyet Farkı</th>
                      <th>Detaylar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pastAudits.map(audit => (
                      <tr key={audit.id}>
                        <td style={{ fontWeight: '500' }}>
                          {new Date(audit.date).toLocaleDateString('tr-TR', {
                            year: 'numeric', month: 'long', day: 'numeric',
                            hour: '2-digit', minute: '2-digit'
                          })}
                        </td>
                        <td style={{ color: 'var(--text-muted)' }}>{audit.notes || 'Açıklama belirtilmedi'}</td>
                        <td style={{ 
                          textAlign: 'right', 
                          fontWeight: '700',
                          color: parseFloat(audit.total_variance_amount) === 0 
                            ? 'var(--text-muted)' 
                            : parseFloat(audit.total_variance_amount) > 0 
                              ? 'var(--success)' 
                              : 'var(--danger)'
                        }}>
                          {parseFloat(audit.total_variance_amount) > 0 ? '+' : ''}
                          {parseFloat(audit.total_variance_amount).toLocaleString('tr-TR')} ₺
                        </td>
                        <td>
                          <div style={{ fontSize: '11px', color: 'var(--primary)', cursor: 'pointer' }} onClick={() => alert(
                            `Sayım Detayları:\n` + 
                            (audit.items && audit.items.length > 0
                              ? audit.items.map(item => `• ${item.ingredient_name}: Sistem: ${parseFloat(item.system_stock)} Sayılan: ${parseFloat(item.actual_stock)} Fark: ${parseFloat(item.variance)} Fiyat Farkı: ${parseFloat(item.cost_difference)} ₺`).join('\n')
                              : 'Sayım detayı bulunamadı')
                          )}>
                            Detayları Göster
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>
      )}

    </div>
  );
}
