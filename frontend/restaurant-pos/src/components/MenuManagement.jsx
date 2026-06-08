import React, { useState, useEffect } from 'react';
import { useResponsive } from '../hooks/useResponsive';
import { Plus, Trash2, Edit2, Check, X } from 'lucide-react';

import { apiFetch, API_BASE } from '../lib/apiClient';

export default function MenuManagement() {
  const { isMobile } = useResponsive();
  const [categories, setCategories] = useState([]);
  const [menuItems, setMenuItems] = useState([]);
  const [activeTab, setActiveTab] = useState('items'); // 'items' | 'categories' | 'modifiers'

  // Modifier state
  const [selectedItemForMod, setSelectedItemForMod] = useState('');
  const [modName, setModName] = useState('');
  const [modPrice, setModPrice] = useState('0');
  const [modRequired, setModRequired] = useState(false);
  const [itemModifiers, setItemModifiers] = useState([]);
  
  // Category Form State
  const [catName, setCatName] = useState('');
  const [catIcon, setCatIcon] = useState('utensils');
  
  // MenuItem Form State
  const [itemName, setItemName] = useState('');
  const [itemPrice, setItemPrice] = useState('');
  const [itemDesc, setItemDesc] = useState('');
  const [itemCat, setItemCat] = useState('');
  const [itemAvail, setItemAvail] = useState(true);
  const [editingItemId, setEditingItemId] = useState(null);
  const [itemImage, setItemImage] = useState(null);

  useEffect(() => {
    fetchCategories();
    fetchMenuItems();
  }, []);

  const fetchItemModifiers = async (itemId) => {
    if (!itemId) return;
    try {
      const res = await apiFetch(`/menu-item-modifiers/?menu_item=${itemId}`);
      const data = await res.json();
      setItemModifiers(data);
    } catch (err) { console.error(err); }
  };

  const handleAddModifier = async (e) => {
    e.preventDefault();
    if (!selectedItemForMod || !modName.trim()) return;
    try {
      const res = await apiFetch(`/menu-item-modifiers/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          menu_item: parseInt(selectedItemForMod),
          name: modName.trim(),
          price_extra: parseFloat(modPrice) || 0,
          is_required: modRequired,
          is_available: true
        })
      });
      if (res.ok) {
        setModName('');
        setModPrice('0');
        setModRequired(false);
        fetchItemModifiers(selectedItemForMod);
      }
    } catch (err) { console.error(err); }
  };

  const handleDeleteModifier = async (id) => {
    try {
      await apiFetch(`/menu-item-modifiers/${id}/`, { method: 'DELETE' });
      fetchItemModifiers(selectedItemForMod);
    } catch (err) { console.error(err); }
  };

  const handleToggleModifierAvail = async (mod) => {
    try {
      await apiFetch(`/menu-item-modifiers/${mod.id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_available: !mod.is_available })
      });
      fetchItemModifiers(selectedItemForMod);
    } catch (err) { console.error(err); }
  };

  const fetchCategories = async () => {
    try {
      const res = await apiFetch(`/categories/`);
      const data = await res.json();
      setCategories(data);
      if (data.length > 0 && !itemCat) {
        setItemCat(data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchMenuItems = async () => {
    try {
      const res = await apiFetch(`/menu-items/`);
      const data = await res.json();
      setMenuItems(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateCategory = async (e) => {
    e.preventDefault();
    if (!catName.trim()) return;

    try {
      const res = await apiFetch(`/categories/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: catName, icon: catIcon })
      });
      if (res.ok) {
        setCatName('');
        fetchCategories();
        alert('Kategori başarıyla eklendi.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteCategory = async (id) => {
    if (!confirm('Bu kategoriyi silmek istediğinize emin misiniz? Kategorideki ürünler de etkilenecektir.')) return;
    try {
      const res = await apiFetch(`/categories/${id}/`, { method: 'DELETE' });
      if (res.ok) {
        fetchCategories();
        fetchMenuItems();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveMenuItem = async (e) => {
    e.preventDefault();
    if (!itemName.trim() || !itemPrice || !itemCat) {
      alert('Lütfen gerekli alanları doldurun.');
      return;
    }

    const formData = new FormData();
    formData.append('name', itemName);
    formData.append('price', parseFloat(itemPrice));
    formData.append('description', itemDesc);
    formData.append('category', parseInt(itemCat));
    formData.append('is_available', itemAvail);
    if (itemImage) {
      formData.append('image', itemImage);
    }

    try {
      let res;
      if (editingItemId) {
        // Edit mode
        res = await apiFetch(`/menu-items/${editingItemId}/`, {
          method: 'PUT',
          body: formData
        });
      } else {
        // Create mode
        res = await apiFetch(`/menu-items/`, {
          method: 'POST',
          body: formData
        });
      }

      if (res.ok) {
        setItemName('');
        setItemPrice('');
        setItemDesc('');
        setItemAvail(true);
        setItemImage(null);
        setEditingItemId(null);
        // Reset file input value
        const fileInput = document.getElementById('item-image-input');
        if (fileInput) fileInput.value = '';
        
        fetchMenuItems();
        alert(editingItemId ? 'Ürün güncellendi.' : 'Ürün başarıyla eklendi.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleEditMenuItem = (item) => {
    setEditingItemId(item.id);
    setItemName(item.name);
    setItemPrice(item.price);
    setItemDesc(item.description || '');
    setItemCat(item.category);
    setItemAvail(item.is_available);
  };

  const handleDeleteMenuItem = async (id) => {
    if (!confirm('Bu ürünü silmek istediğinize emin misiniz?')) return;
    try {
      const res = await apiFetch(`/menu-items/${id}/`, { method: 'DELETE' });
      if (res.ok) {
        fetchMenuItems();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCancelEdit = () => {
    setEditingItemId(null);
    setItemName('');
    setItemPrice('');
    setItemDesc('');
    setItemAvail(true);
    setItemImage(null);
    const fileInput = document.getElementById('item-image-input');
    if (fileInput) fileInput.value = '';
  };

  return (
    <div>
      {/* Sub-navigation Tabs */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginBottom: '24px' }}>
        <button
          className={`btn ${activeTab === 'items' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('items')}
          style={{ padding: '8px 16px', fontSize: '13px' }}
        >
          Ürün Yönetimi
        </button>
        <button
          className={`btn ${activeTab === 'categories' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('categories')}
          style={{ padding: '8px 16px', fontSize: '13px' }}
        >
          Kategori Yönetimi
        </button>
        <button
          className={`btn ${activeTab === 'modifiers' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('modifiers')}
          style={{ padding: '8px 16px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          ➕ Seçenek / Modifier
        </button>
      </div>

      {activeTab === 'items' ? (
        <div className="menu-mgmt-container">
          {/* Menu Item Form */}
          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>
              {editingItemId ? 'Ürünü Düzenle' : 'Yeni Ürün Ekle'}
            </h3>
            <form onSubmit={handleSaveMenuItem}>
              <div className="form-group">
                <label>Ürün Adı *</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={itemName} 
                  onChange={(e) => setItemName(e.target.value)} 
                  placeholder="örn: Tavuk Şiş"
                  required
                />
              </div>

              <div className="form-group">
                <label>Kategori *</label>
                <select 
                  className="form-control form-select" 
                  value={itemCat} 
                  onChange={(e) => setItemCat(e.target.value)}
                  required
                >
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Fiyat (TL) *</label>
                <input 
                  type="number" 
                  step="0.01"
                  className="form-control" 
                  value={itemPrice} 
                  onChange={(e) => setItemPrice(e.target.value)} 
                  placeholder="örn: 220.00"
                  required
                />
              </div>

              <div className="form-group">
                <label>Açıklama</label>
                <textarea 
                  className="form-control" 
                  rows="3"
                  value={itemDesc} 
                  onChange={(e) => setItemDesc(e.target.value)} 
                  placeholder="Garnitür vb. açıklamalar..."
                />
              </div>

              <div className="form-group">
                <label>Ürün Resmi</label>
                <input 
                  type="file" 
                  id="item-image-input"
                  className="form-control" 
                  accept="image/*"
                  onChange={(e) => setItemImage(e.target.files[0])} 
                />
              </div>

              <div className="checkbox-group" style={{ marginBottom: '24px' }}>
                <input 
                  type="checkbox" 
                  id="itemAvail"
                  checked={itemAvail} 
                  onChange={(e) => setItemAvail(e.target.checked)} 
                />
                <label htmlFor="itemAvail" style={{ cursor: 'pointer', fontSize: '14px' }}>Satışa Açık</label>
              </div>

              <div style={{ display: 'flex', gap: '12px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 2 }}>
                  {editingItemId ? 'Güncelle' : 'Ürünü Kaydet'}
                </button>
                {editingItemId && (
                  <button type="button" className="btn btn-secondary" onClick={handleCancelEdit}>
                    Vazgeç
                  </button>
                )}
              </div>
            </form>
          </div>

          {/* Menu Items Table */}
          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Ürün Listesi</h3>
            <div className="table-container">
              <table className="mgmt-table">
                <thead>
                  <tr>
                    <th>Ürün Adı</th>
                    <th>Kategori</th>
                    <th>Fiyat</th>
                    <th>Durum</th>
                    <th>İşlemler</th>
                  </tr>
                </thead>
                <tbody>
                  {menuItems.map(item => (
                    <tr key={item.id}>
                      <td style={{ fontWeight: '500' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          {item.image ? (
                            <img 
                              src={item.image.startsWith('http') ? item.image : `${(import.meta.env.VITE_API_URL || '')}${item.image}`} 
                              alt={item.name} 
                              style={{ width: '36px', height: '36px', borderRadius: '8px', objectFit: 'cover', border: '1px solid var(--panel-border)' }} 
                            />
                          ) : (
                            <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(0,0,0,0.04)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', color: 'var(--text-muted)' }}>
                              Yok
                            </div>
                          )}
                          <span>{item.name}</span>
                        </div>
                      </td>
                      <td>{item.category_name}</td>
                      <td>{parseFloat(item.price).toLocaleString('tr-TR')} ₺</td>
                      <td>
                        <span className={`badge ${item.is_available ? 'badge-success' : 'badge-danger'}`}>
                          {item.is_available ? 'Satışta' : 'Kapalı'}
                        </span>
                      </td>
                      <td>
                        <button className="action-icon-btn" onClick={() => handleEditMenuItem(item)}>
                          <Edit2 size={16} />
                        </button>
                        <button className="action-icon-btn delete" onClick={() => handleDeleteMenuItem(item.id)}>
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="menu-mgmt-container" style={{ gridTemplateColumns: isMobile ? '1fr' : '1fr 1.5fr' }}>
          {/* Category Form */}
          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Yeni Kategori Ekle</h3>
            <form onSubmit={handleCreateCategory}>
              <div className="form-group">
                <label>Kategori Adı</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={catName} 
                  onChange={(e) => setCatName(e.target.value)} 
                  placeholder="örn: Çorbalar"
                  required
                />
              </div>

              <div className="form-group">
                <label>Sembol (İkon)</label>
                <select 
                  className="form-control form-select" 
                  value={catIcon} 
                  onChange={(e) => setCatIcon(e.target.value)}
                >
                  <option value="soup">Soup (Çorba)</option>
                  <option value="utensils">Utensils (Yemek)</option>
                  <option value="salad">Salad (Salata)</option>
                  <option value="cake">Cake (Tatlı)</option>
                  <option value="cup-soda">Soda (İçecek)</option>
                </select>
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '8px' }}>
                Kategori Oluştur
              </button>
            </form>
          </div>

          {/* Categories List */}
          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Kategoriler</h3>
            <div className="table-container">
              <table className="mgmt-table">
                <thead>
                  <tr>
                    <th>Sembol</th>
                    <th>Kategori Adı</th>
                    <th>İşlem</th>
                  </tr>
                </thead>
                <tbody>
                  {categories.map(cat => (
                    <tr key={cat.id}>
                      <td style={{ fontSize: '18px' }}>
                        {cat.icon === 'soup' ? '🥣' : cat.icon === 'salad' ? '🥗' : cat.icon === 'cake' ? '🍰' : cat.icon === 'cup-soda' ? '🥤' : '🍔'}
                      </td>
                      <td style={{ fontWeight: '500' }}>{cat.name}</td>
                      <td>
                        <button className="action-icon-btn delete" onClick={() => handleDeleteCategory(cat.id)}>
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── MODIFIER TAB ── */}
      {activeTab === 'modifiers' && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '340px 1fr', gap: isMobile ? '16px' : '24px' }}>
          {/* Add Modifier Form */}
          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Seçenek Ekle</h3>
            <form onSubmit={handleAddModifier} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div className="form-group">
                <label>Ürün Seç</label>
                <select
                  className="form-control form-select"
                  value={selectedItemForMod}
                  onChange={(e) => { setSelectedItemForMod(e.target.value); fetchItemModifiers(e.target.value); }}
                  required
                >
                  <option value="">-- Ürün seçin --</option>
                  {menuItems.map(item => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Seçenek Adı</label>
                <input
                  type="text"
                  className="form-control"
                  value={modName}
                  onChange={(e) => setModName(e.target.value)}
                  placeholder="Örn: Ekstra Peynir, Büyük Boy"
                  required
                />
              </div>
              <div className="form-group">
                <label>Ekstra Fiyat (₺)</label>
                <input
                  type="number"
                  step="0.50"
                  className="form-control"
                  value={modPrice}
                  onChange={(e) => setModPrice(e.target.value)}
                  placeholder="0 = Ücretsiz"
                />
              </div>
              <div className="checkbox-group">
                <input
                  type="checkbox"
                  id="modRequired"
                  checked={modRequired}
                  onChange={(e) => setModRequired(e.target.checked)}
                />
                <label htmlFor="modRequired" style={{ cursor: 'pointer', fontSize: '13px' }}>Zorunlu Seçim</label>
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={!selectedItemForMod}>
                <Plus size={16} /> Seçeneği Ekle
              </button>
            </form>
          </div>

          {/* Modifier List */}
          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>
              {selectedItemForMod
                ? `${menuItems.find(i => i.id === parseInt(selectedItemForMod))?.name || ''} — Seçenekler`
                : 'Seçenekler'}
            </h3>
            {!selectedItemForMod ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', fontSize: '13px' }}>
                Sol taraftan bir ürün seçin
              </div>
            ) : itemModifiers.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', fontSize: '13px' }}>
                Bu ürüne henüz seçenek eklenmedi
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {itemModifiers.map(mod => (
                  <div key={mod.id} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '12px 14px', borderRadius: '10px',
                    border: '1px solid var(--panel-border)',
                    background: mod.is_available ? 'rgba(0,0,0,0.02)' : 'rgba(0,0,0,0.01)',
                    opacity: mod.is_available ? 1 : 0.5
                  }}>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '13px' }}>{mod.name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                        {parseFloat(mod.price_extra) > 0 ? `+${parseFloat(mod.price_extra).toLocaleString('tr-TR')} ₺` : 'Ücretsiz'}
                        {mod.is_required && <span style={{ marginLeft: '8px', color: '#f59e0b' }}>• Zorunlu</span>}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <button
                        onClick={() => handleToggleModifierAvail(mod)}
                        className={`badge ${mod.is_available ? 'badge-success' : 'badge-warning'}`}
                        style={{ border: 'none', cursor: 'pointer', padding: '3px 8px', fontSize: '11px' }}
                      >
                        {mod.is_available ? 'Aktif' : 'Pasif'}
                      </button>
                      <button className="action-icon-btn delete" onClick={() => handleDeleteModifier(mod.id)}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
